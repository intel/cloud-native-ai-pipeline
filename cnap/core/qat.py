"""A QAT module.

This module provides a class to use Intel qat to accelerate compression/decompression of frames.
It provides methods to init, set up, teardown and close QATzip session, as well as compression 
and decompression using QAT.

Classes:
    QATZip: A class that use QAT to accelerate frame compression and decompression.
"""
import ctypes
import logging
import time
from core.qat_params import QzSession, QzSessionParamsCommon, QzSessionParamsDeflate

LOG = logging.getLogger(__name__)
qziplib = ctypes.cdll.LoadLibrary("libqatzip.so")


class QATZip:
    """A class that use QAT to accelerate frame compression and decompression..

    Attributes:
        _direction (int): The QATzip work way. 
        _comp_lvl (int): The QATzip compression level.
        _algorithm (int): The QATzip Compression/decompression algorithm.
        _session (QzSession): The QATzip Session.
        _common_session (QzSessionParamsCommon): The QATzip session with common parameters.
        _deflate_params (QzSessionParamsDeflate): The QATzip session with deflate parameters.
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

    #QATzip compression algorithm: deflate.
    ALGO_DEFLATE = 8

    def __init__(self,
                 direction: int = DIR_BOTH,
                 comp_lvl: int = LEVEL_FAST,
                 algorithm: int = ALGO_DEFLATE):
        """Initialize a QATzip object.

        This constructor initializes a QATzip object with the given direction, compresion level 
        and algorithm.

        Args:
            direction (int): The QATzip work way: DIR_COMPRESS, DIR_DECOMPRESS, or DIR_BOTH. 
            comp_lvl (int): The QATzip compression level(from 1 to 9).
            algorithm (int): The QATzip Compression/decompression algorithm(only ALGO_DEFLATE now).  
        """
        self._direction = direction
        self._comp_lvl = comp_lvl
        self._algorithm = algorithm
        self._session = QzSession()
        self._common_params = QzSessionParamsCommon(direction = ctypes.c_uint(self._direction),
                                                    comp_lvl = ctypes.c_ubyte(self._comp_lvl),
                                                    comp_algorithm = ctypes.c_uint(self._algorithm))
        self._deflate_params = QzSessionParamsDeflate(common_params = self._common_params)
        self.init_session()
        self.set_session()

    @property
    def direction(self) -> int:
        """int: Compress or decompress or both."""
        return self._direction

    @property
    def comp_lvl(self) -> int:
        """int: The QATzip compression level."""
        return self._comp_lvl

    @property
    def algorithm(self) -> int:
        """int: The QATzip compression/decompression algorithm."""
        return self._algorithm

    def init_session(self) -> None:
        """Initialize QAT hardware.

        Raises:
            RuntimeError: If any errors during the initialization of QAT. 
        """
        ret = qziplib.qzInit(ctypes.byref(self._session), self.SW_BACKUP)
        if ret != 0:
            LOG.error("Failed to initialize the QATzip session: %s", ret)
            raise RuntimeError(f"Initialize QATzip session failed with status:{ret}.")
        LOG.info("Initialize QAT hardware successful.")

    def set_session(self) -> None:
        """Initialize a QATzip session with deflate parameters.
        
        Raises:
            RuntimeError: If any error occurs during the session set up. 
        """
        ret = qziplib.qzSetupSessionDeflate(
            ctypes.byref(self._session),
            ctypes.byref(self._deflate_params))
        if ret != 0:
            LOG.error("Failed to setup the QATzip session: %s.", ret)
            raise RuntimeError(f"Set QATzip session failed with status: {ret}.")
        LOG.info("Set up QAT session successful.")

    def teardown_session(self) -> None:
        """Uninitialize a QATzip session.

        This method disconnects a session from a hardware instance and deallocates buffers. 
        If no session has been initialized, then no action will take place.
        
        Raises:
            RuntimeError: If any error occurs during the session teardown. 
        """
        ret = qziplib.qzTeardownSession(ctypes.byref(self._session))
        if ret != 0:
            LOG.error("Failed to teardown the QATzip session: %s.", ret)
            raise RuntimeError(f"Teardown the QATzip session failed with status: {ret}.")

    def close_session(self) -> None:
        """Terminates a QATzip session.
        
        This method closes the connection with QAT.
        
        Raises:
            RuntimeError: If any error occurs while closing the session. 
        """
        ret = qziplib.qzClose(ctypes.byref(self._session))
        if ret != 0:
            LOG.error("Failed to close the QATzip session: %s.", ret)
            raise RuntimeError(f"Close the QATzip session failed with status: {ret}.")

    def compress(self, src: bytes) -> bytes:
        """Use QAT to accelerate frame compression.

        Args:
            src (bytes): Frame that need to be compressed.

        Returns:
            bytes: Compressed Frame.
        
        Raises:
            OverflowError: If compression integer overflow occurs.
            ValueError: If the compression input length is invalid.
            RuntimeError: If any error occurs during compression.
        """
        dst_sz = qziplib.qzMaxCompressedLength(len(src), ctypes.byref(self._session))
        if dst_sz == 0:
            LOG.error("Compression integer overflow happens.")
            raise OverflowError("Compression integer overflow happens.")
        if dst_sz == 34:
            LOG.error("Compression input length is 0.")
            raise ValueError("Invalid compression input length.")

        #preprocessing: Convert src/dst to ctypes
        src_len = ctypes.c_uint(len(src))
        src_array = (ctypes.c_char * len(src))(*src)
        src_point = ctypes.cast(ctypes.pointer(src_array),ctypes.c_void_p)

        dst_len = ctypes.c_uint(dst_sz)
        dst_bytes_array = (ctypes.c_char *dst_sz)()
        dst_point = ctypes.cast(ctypes.pointer(dst_bytes_array), ctypes.c_void_p)

        start_time = time.time()

        ret = qziplib.qzCompress(
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
        """Use QAT to accelerate frame decompression.

        Args:
            src (bytes): Frame that need to be decompressed.

        Returns:
            bytes: Decompressed Frame.
        
        Raises:
            RuntimeError: If any error occurs during decompression. 
        """
        #preprocessing: Convert src/dst to ctypes
        dst_sz =  len(src) * self.EXPANSION_RATIO[0]

        src_len = ctypes.c_uint(len(src))
        src_array = (ctypes.c_char * len(src))(*src)
        src_point = ctypes.cast(ctypes.pointer(src_array),ctypes.c_void_p)

        dst_len = ctypes.c_uint(dst_sz)
        dst_bytes_array = (ctypes.c_char *dst_sz)()
        dst_point = ctypes.cast(ctypes.pointer(dst_bytes_array), ctypes.c_void_p)

        start_time = time.time()

        ret = qziplib.qzDecompress(
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
