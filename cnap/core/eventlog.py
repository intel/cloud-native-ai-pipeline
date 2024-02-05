"""A EventLog module.

This module provides functions related to event log processing. The event log can be fetched by
Confidential Cloud-Native Primitives (CCNP), and is defined according to several tcg supported event
log formats defined in TCG_PCClient Spec, Canonical Eventlog Spec, etc.

CCNP: https://github.com/cc-api/confidential-cloud-native-primitives
TCG_PCClient Spec:
  https://trustedcomputinggroup.org/wp-content/uploads/TCG_PCClientSpecPlat_TPM_2p0_1p04_pub.pdf
Canonical Eventlog Spec:
  https://trustedcomputinggroup.org/wp-content/uploads/TCG_IWG_CEL_v1_r0p41_pub.pdf

Functions:
    replay_event_log: Replay event logs by IMR index.
    verify_event_log: Verify event log by comparing IMR value from CCNP fetching and replayed from
      event log.
"""
import logging
import base64
from hashlib import sha1, sha256, sha384, sha512

from ccnp.eventlog.eventlog_sdk import CCEventLogEntry, CCAlgorithms
from ccnp import Measurement, MeasurementType

LOG = logging.getLogger(__name__)

IMR_VERIFY_COUNT = 3

def replay_event_log(event_logs: list[CCEventLogEntry]) -> dict:
    """Replay event logs by Integrated Measurement Register (IMR) index.

    Args:
        event_logs (list[CCEventLogEntry]): Event logs fetched by CCNP.

    Returns:
        dict: A dictionary containing the replay result displayed by IMR index and hash algorithm. 
        Layer 1 key of the dict is the IMR index, the value is another dict which using the hash 
        algorithm as the key and the replayed measurement as value.
        Sample value:
            { 0: { 12: <measurement_replayed>}}
    """
    measurement_dict = {}
    for event_log in event_logs:
        # pylint: disable-next=consider-iterating-dictionary
        if event_log.reg_idx not in measurement_dict.keys():
            measurement_dict[event_log.reg_idx] = {}

        alg_id = event_log.alg_id.algo_id
        # Check algorithm type and prepare for replay
        if alg_id == CCAlgorithms.ALG_SHA1:
            algo = sha1()
        elif alg_id == CCAlgorithms.ALG_SHA384:
            algo = sha384()
        elif alg_id == CCAlgorithms.ALG_SHA256:
            algo = sha256()
        elif alg_id == CCAlgorithms.ALG_SHA512:
            algo = sha512()
        else:
            LOG.error("Unsupported hash algorithm %d", alg_id)
            continue

        # Initialize value if alg_id not found in dict
        if alg_id not in measurement_dict[event_log.reg_idx].keys():
            measurement_dict[event_log.reg_idx][alg_id] = bytearray(
                event_log.alg_id.digest_size)

        # Do replay and update the result into dict
        digest = list(map(int, event_log.digest.strip('[]').split(' ')))
        # pylint: disable-next=consider-using-f-string
        digest_hex = ''.join('{:02x}'.format(i) for i in digest)
        algo.update(measurement_dict[event_log.reg_idx][alg_id] + bytes.fromhex(digest_hex))
        measurement_dict[event_log.reg_idx][alg_id] = algo.digest()

    return measurement_dict

def verify_event_log(measurement_dict: dict) -> bool:
    """Verify event log by comparing IMR value from CCNP fetching and replayed via event log.

    IMR: Integrated Measurement Register.

    Args:
        measurement_dict (dict): The event logs replay result displayed by IMR index and hash
          algorithm.

    Returns:
        bool: True if event log verify success, False if event log verify failed.
    """
    LOG.info("Verify IMR measurement value and replayed value from event logs")
    for index in range(IMR_VERIFY_COUNT):
        # Fectch IMR measurement
        LOG.info("Fetch measurements in IMR[%d]", index)
        imr_measurement = base64.b64decode(Measurement.get_platform_measurement(
            MeasurementType.TYPE_TDX_RTMR, None, index))
        LOG.info("IMR[%d](measurement): %s", index, imr_measurement.hex())

        # Get IMR value from replayed event log
        if index not in measurement_dict or measurement_dict[index] == {}:
            LOG.error("IMR[%d] verify failed, the replayed value from event logs doesn't exist",
                index)
            return False
        for value in measurement_dict[index].values():
            imr_replayed = value
            break

        LOG.info("IMR[%d](replayed): %s", index, imr_replayed.hex())
        if imr_measurement == imr_replayed:
            LOG.info("IMR[%d] passed the verification.", index)
        else:
            LOG.error("IMR[%d] did not pass the verification.", index)
            return False

    return True
