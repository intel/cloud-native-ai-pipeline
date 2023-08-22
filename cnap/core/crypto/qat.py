"""A QAT module.

This module provides a class to use Intel qat to accelerate compression/decompression of frames.
It provides methods to init, set up, teardown and close QATZip session, as well as compression
and decompression using QAT.

Classes:
    QATZip: A class that use QAT to accelerate frame compression and decompression.
"""
import ctypes
import logging
import time

from core.crypto.qat_params import QzSession, QzSessionParamsCommon, QzSessionParamsDeflate
from core.crypto.zip import ZipBase

LOG = logging.getLogger(__name__)


class QATZip(ZipBase):
    """A class that use QAT to accelerate frame compression and decompression.

    Attributes:
        _qziplib (CDLL): The QATZip library.
        _direction (int): The QATZip work way.
        _comp_lvl (int): The QATZip compression level.
        _algorithm (int): The QATZip Compression/decompression algorithm.
        _session (QzSession): The QATZip Session.
        _common_session (QzSessionParamsCommon): The QATZip session with common parameters.
        _deflate_params (QzSessionParamsDeflate): The QATZip session with deflate parameters.
    """

    #Enbale SW backup.
    SW_BACKUP = 1
    #No more data to be compressed.
    LAST = 1
    #Estimate maximum data expansion after decompression.
    EXPANSION_RATIO = [5, 20, 50, 100]

    #Session will be used for compression.
    DIR_COMPRESS = 0
    #Session will be used for decompression.
    DIR_DECOMPRESS = 1
    #Session will be used for both compression and decompression.
    DIR_BOTH = 2

    #Compression level - compress faster.
    LEVEL_FAST = 1
    #Compression level - compress better.
    LEVEL_BEST = 9

    #QATZip compression algorithm: deflate.
    ALGO_DEFLATE = 8

    def __init__(self,
                 direction: int = DIR_BOTH,
                 comp_lvl: int = LEVEL_FAST,
                 algorithm: int = ALGO_DEFLATE):
        """Initialize a QATZip object.

        This constructor initializes a QATZip object with the given direction, compresion level
        and algorithm.

        Args:
            direction (int): The QATZip work way: DIR_COMPRESS, DIR_DECOMPRESS, or DIR_BOTH.
            comp_lvl (int): The QATZip compression level(from 1 to 9).
            algorithm (int): The QATZip Compression/decompression algorithm(only ALGO_DEFLATE now).
        """
        self._qziplib = ctypes.cdll.LoadLibrary("libqatzip.so")
        self._direction = direction
        self._comp_lvl = comp_lvl
        self._algorithm = algorithm
        self._session = QzSession()
        self._common_params = QzSessionParamsCommon(direction=ctypes.c_uint(self._direction),
                                                    comp_lvl=ctypes.c_ubyte(self._comp_lvl),
                                                    comp_algorithm=ctypes.c_uint(self._algorithm))
        self._deflate_params = QzSessionParamsDeflate(common_params=self._common_params)
        self.init_session()
        self.set_session()

    @property
    def direction(self) -> int:
        """int: Compress or decompress or both."""
        return self._direction

    @property
    def comp_lvl(self) -> int:
        """int: The QATZip compression level."""
        return self._comp_lvl

    @property
    def algorithm(self) -> int:
        """int: The QATZip compression/decompression algorithm."""
        return self._algorithm

    def init_session(self) -> None:
        """Initialize QAT hardware.

        Raises:
            RuntimeError: If any errors during the initialization of QAT.
        """
        ret = self._qziplib.qzInit(ctypes.byref(self._session), self.SW_BACKUP)
        if ret != 0:
            LOG.error("Failed to initialize the QATZip session: %s", ret)
            raise RuntimeError(f"Initialize QATZip session failed with status:{ret}.")
        LOG.info("Initialize QAT hardware successful.")

    def set_session(self) -> None:
        """Initialize a QATZip session with deflate parameters.

        Raises:
            RuntimeError: If any error occurs during the session set up.
        """
        ret = self._qziplib.qzSetupSessionDeflate(
            ctypes.byref(self._session),
            ctypes.byref(self._deflate_params))
        if ret != 0:
            LOG.error("Failed to setup the QATZip session: %s.", ret)
            raise RuntimeError(f"Set QATZip session failed with status: {ret}.")
        LOG.info("Set up QAT session successful.")

    def teardown_session(self) -> None:
        """Uninitialize a QATZip session.

        This method disconnects a session from a hardware instance and deallocates buffers.
        If no session has been initialized, then no action will take place.

        Raises:
            RuntimeError: If any error occurs during the session teardown.
        """
        ret = self._qziplib.qzTeardownSession(ctypes.byref(self._session))
        if ret != 0:
            LOG.error("Failed to teardown the QATZip session: %s.", ret)
            raise RuntimeError(f"Teardown the QATZip session failed with status: {ret}.")

    def close_session(self) -> None:
        """Terminates a QATZip session.

        This method closes the connection with QAT.

        Raises:
            RuntimeError: If any error occurs while closing the session.
        """
        ret = self._qziplib.qzClose(ctypes.byref(self._session))
        if ret != 0:
            LOG.error("Failed to close the QATZip session: %s.", ret)
            raise RuntimeError(f"Close the QATZip session failed with status: {ret}.")

    def compress(self, src: bytes) -> bytes:
        """See base class."""
        dst_sz = self._qziplib.qzMaxCompressedLength(len(src), ctypes.byref(self._session))
        if dst_sz == 0:
            LOG.error("Compression integer overflow happens.")
            raise OverflowError("Compression integer overflow happens.")
        if dst_sz == 34:
            LOG.error("Compression input length is 0.")
            raise ValueError("Invalid compression input length.")

        #preprocessing: Convert src/dst to ctypes
        src_len = ctypes.c_uint(len(src))
        src_array = (ctypes.c_char * len(src))(*src)
        src_point = ctypes.cast(ctypes.pointer(src_array), ctypes.c_void_p)

        dst_len = ctypes.c_uint(dst_sz)
        dst_bytes_array = (ctypes.c_char *dst_sz)()
        dst_point = ctypes.cast(ctypes.pointer(dst_bytes_array), ctypes.c_void_p)

        start_time = time.time()

        ret = self._qziplib.qzCompress(
            ctypes.byref(self._session),
            src_point, ctypes.byref(src_len),
            dst_point, ctypes.byref(dst_len),
            self.LAST)
        if ret != 0:
            LOG.error("Failed to compress: %s.", ret)
            raise RuntimeError(f"Compression failed with status: {ret}.")

        end_time = time.time()
        time_cost = end_time- start_time

        LOG.debug("Compress %d bytes in %d bytes, cost %fs", len(src), dst_len.value, time_cost)
        return bytes(dst_bytes_array.raw[:dst_len.value])

    def decompress(self, src: bytes) -> bytes:
        """See base class."""
        #preprocessing: Convert src/dst to ctypes
        dst_sz = len(src) * self.EXPANSION_RATIO[0]

        src_len = ctypes.c_uint(len(src))
        src_array = (ctypes.c_char * len(src))(*src)
        src_point = ctypes.cast(ctypes.pointer(src_array), ctypes.c_void_p)

        dst_len = ctypes.c_uint(dst_sz)
        dst_bytes_array = (ctypes.c_char *dst_sz)()
        dst_point = ctypes.cast(ctypes.pointer(dst_bytes_array), ctypes.c_void_p)

        start_time = time.time()

        ret = self._qziplib.qzDecompress(
            ctypes.byref(self._session),
            src_point, ctypes.byref(src_len),
            dst_point, ctypes.byref(dst_len))
        if ret != 0:
            LOG.error("Failed to decompress: %s.", ret)
            raise RuntimeError(f"Decompression failed with status: {ret}.")

        end_time = time.time()
        time_cost = end_time - start_time

        LOG.debug("Decompress %d bytes in %d bytes, cost %fs", len(src), dst_len.value, time_cost)
        return bytes(dst_bytes_array.raw[:dst_len.value])

    def __del__(self):
        """Ensure the release of each session."""
        try:
            self.teardown_session()
            self.close_session()
        except RuntimeError as e:
            LOG.error("Error during releasing session: %s", e)
