"""A QAT params module.

This module provides the relevant parameters required to call QAT.

Classes:
    QzDirection: An enum for the type of the Huffman header supported by QATzip.
    QzPollingMode: An enum for the type of polling mode supported by QATzip.
    QzDataFormat: An enum for the type of data format supported by QATzip.
    QzHuffmanHdr: An enum for the type of the Huffman header supported by QATzip.
    QzSession:A class for QATzip Session opaque data storage.
    QzSessionParamsCommon: A class for QATzip session common parameters.
    QzSessionParamsDeflate: A class for QATzip session defalte parameters.
"""

import ctypes
from enum import Enum

class QzDirection(Enum):
    """An enum for the type of QzDirection.
    
    This enum defines the types of QzDirection that can be created.
    """

    QZ_DIR_COMPRESS = ctypes.c_uint(0)
    QZ_DIR_DECOMPRESS = ctypes.c_uint(1)
    QZ_DIR_BOTH = ctypes.c_uint(2)

class QzPollingMode(Enum):
    """An enum for the type of QzPollingMode.
    
    This enum defines the types of polling mode supported by QATzip.
    """

    QZ_PERIODICAL_POLLING = ctypes.c_uint(0)
    QZ_BUSY_POLLING = ctypes.c_uint(1)

class QzDataFormat(Enum):
    """An enum for the type of QzDataFormat.
    
    This enum defines the types of the data format supported by QATzip.
    """

    QZ_DEFLATE_4B = ctypes.c_uint(0)
    QZ_DEFLATE_GZIP = ctypes.c_uint(1)
    QZ_DEFLATE_GZIP_EXT = ctypes.c_uint(2)
    QZ_DEFLATE_RAW = ctypes.c_uint(3)
    QZ_FMT_NUM =  ctypes.c_uint(4)

class QzHuffmanHdr(Enum):
    """An enum for the type of QzipHuffmanHdr.
    
    This enum defines the types of the Huffman header supported by QATzip.
    """

    QZ_DYNAMIC_HDR = ctypes.c_uint(0)
    QZ_STATIC_HDR = ctypes.c_uint(1)

class QzSession(ctypes.Structure):
    """A class for QATzip Session opaque data storage.
    
    This class contains a pointer to a structure with session state.
    
    Attributes:
        hw_session_stat (ctypes.c_long): Hardware session status.
        thd_sess_stst (ctypes.c_int): Note process compression and decompression thread state.
        internel (ctypes.c_void_p): Session data is opaque to outside world.
        total_in (ctypes.c_ulong): Total processed input data length in this session.
        total_out(ctypes.c_ulong): Total output data length in this session.
    """

    _fields_ = [
        ('hw_session_stat', ctypes.c_long),
        ('thd_sess_stst', ctypes.c_int),
        ('internel', ctypes.c_void_p),
        ('total_in', ctypes.c_ulong),
        ('total_out', ctypes.c_ulong),
    ]

    def __init__(self, **kwargs):
        """Initialize the QzSession with default value."""
        self.hw_session_stat = kwargs.get('hw_session_stat', 1)
        self.thd_sess_stst = kwargs.get('thd_sess_stst', 0)
        self.internel = kwargs.get('internel', None)
        self.total_in = kwargs.get('total_in', 0)
        self.total_out = kwargs.get('total_out', 0)

class QzSessionParamsCommon(ctypes.Structure):
    """A class for QATzip session common parameters.
    
    This structure contains data for initializing a common session..
    
    Attributes:
        direction (ctypes.c_uint): Compress or decompress.
        comp_lvl (ctypes.c_ubyte): Compression level 1 to 9.
        comp_algorithm (ctypes.c_uint): Compress/decompression algorithms.
        max_forks (ctypes.c_uint): Maximum forks permitted in the current thread.
        sw_backup (ctypes.c_ubyte): Bit field defining SW configuration.
        hw_buff_sz (ctypes.c_uint): Default buffer size, must be a power of 2k.
        strm_buff_sz (ctypes.c_uint): Default strm_buf_sz, equals to hw_buff_sz.
        input_sz_thrshold (ctypes.c_uint): Threshold of compression service's input size.
        req_cnt_thrshold (ctypes.c_uint): Set between 1 and 32.
        wait_cnt_thrshold (ctypes.c_uint): Wait for specific calls before device reopen retry.
        polling_mode (ctypes.c_uint): Polling mode supported by QATzip.
        is_sensitive_mode (ctypes.c_uint): 0 means disable sensitive mode, 1 means enable.
    """

    _fields_ = [
        ('direction', ctypes.c_uint),
        ('comp_lvl', ctypes.c_ubyte),
        ('comp_algorithm', ctypes.c_uint),
        ('max_forks', ctypes.c_uint),
        ('sw_backup', ctypes.c_ubyte),
        ('hw_buff_sz', ctypes.c_uint),
        ('strm_buff_sz', ctypes.c_uint),
        ('input_sz_thrshold', ctypes.c_uint),
        ('req_cnt_thrshold', ctypes.c_uint),
        ('wait_cnt_thrshold', ctypes.c_uint),
        ('polling_mode',ctypes.c_uint),
        ('is_sensitive_mode', ctypes.c_uint),
    ]

    def __init__(self,
                direction: ctypes.c_uint = QzDirection.QZ_DIR_BOTH.value,
                comp_lvl: ctypes.c_ubyte = 1,
                comp_algorithm: ctypes.c_uint = 8,
                max_forks: ctypes.c_uint = 2,
                sw_backup: ctypes.c_ubyte = 1,
                hw_buff_sz: ctypes.c_uint = 64*1024,
                strm_buff_sz: ctypes.c_uint = 64*1024,
                input_sz_thrshold: ctypes.c_uint = 1024,
                req_cnt_thrshold: ctypes.c_uint = 32,
                wait_cnt_thrshold: ctypes.c_uint = 8,
                polling_mode: ctypes.c_uint = QzPollingMode.QZ_PERIODICAL_POLLING.value,
                is_sensitive_mode: ctypes.c_uint = 0):
        """Initialize the QzSessionParamsCommon with default value."""
        self.direction = direction
        self.comp_lvl = comp_lvl
        self.comp_algorithm = comp_algorithm
        self.max_forks = max_forks
        self.sw_backup = sw_backup
        self.hw_buff_sz = hw_buff_sz
        self.strm_buff_sz = strm_buff_sz
        self.input_sz_thrshold = input_sz_thrshold
        self.req_cnt_thrshold = req_cnt_thrshold
        self.wait_cnt_thrshold = wait_cnt_thrshold
        self.polling_mode = polling_mode
        self.is_sensitive_mode = is_sensitive_mode

class QzSessionParamsDeflate(ctypes.Structure):
    """A class for QATzip session deflate parameters.
    
    Attributes:
        common_params (QzSessionParamsCommon): Compress or decompress. 
        huffman_hdr (ctypes.c_uint): Dynamic or Static Huffman headers.
        data_fmt (ctypes.c_uint): Deflate, deflate with GZip or deflate with GZip ext.
               
    """

    _fields_ = [
        ('common_params', QzSessionParamsCommon),
        ('huffman_hdr',ctypes.c_uint),
        ('data_fmt', ctypes.c_uint),
    ]

    def __init__(self,
                common_params: QzSessionParamsCommon = QzSessionParamsCommon(),
                huffman_hdr: QzHuffmanHdr = QzHuffmanHdr.QZ_DYNAMIC_HDR.value,
                data_fmt: QzDataFormat = QzDataFormat.QZ_DEFLATE_GZIP.value):
        """Initialize the QzSessionParamsDeflate with default value."""
        self.common_params = common_params
        self.huffman_hdr = huffman_hdr
        self.data_fmt = data_fmt
