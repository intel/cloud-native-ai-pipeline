"""A Keybroker module.

This module provides an object-oriented design for key broker client to connect with
key broker server (KBS), get model decryption key from the KBS.

Classes:
    KeyBrokerClientBase: An abstract base class for key broker client.
    SimpleKeyBrokerClient: A concrete class implementing the KeyBrokerClientBase to connect
      a simple KBS.
"""

from abc import ABC, abstractmethod
import base64
import logging
import struct
import requests

from ccnp import CcnpSdk
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from core.eventlog import verify_event_log

LOG = logging.getLogger(__name__)

# Set the connection timeout to 10s
TIMEOUT = 10
# Set the connection retry times to 3
RETRY_TIMES=3
# Set http connection succesfull code
HTTP_OK = [200]

class KeyBrokerClientBase(ABC):
    """An abstract base class for key broker client.

    This class serves as a blueprint for subclasses that need to implement
    `get_key` methods for different types of KBS.
    """

    @abstractmethod
    def get_key(self, server_url: str, key_id: str):
        """Get a key from KBS.

        This method is used to get a key from KBS.

        Args:
            server_url (str): The url of KBS.
            key_id (str): The id of the key.

        Raises:
            ValueError: If the server_url or key_id is None.
            RuntimeError: If get quote or get key failed.
            NotImplementedError: If the subclasses don't implement the method.
        """
        raise NotImplementedError("Subclasses should implement get_key() method.")


class SimpleKeyBrokerClient(KeyBrokerClientBase):
    """A implementation for key broker client.

    This class implement `get_key` in `KeyBrokerClientBase` abstract base class to connect
    to a simple KBS.
    Here is an example flow of a simple KBS:
        - Accept a quote and a public key from client.
        - Verify the quote and do attestation, return if verify failed.
        - Get the user key from key management server (KMS), generate a symmetric wrapping
          key (SWK) to encrypt the user key (wrapped_key).
        - Encrypt the SWK by the public key from client (wrapped_swk).
    For a key broker client, here is an example flow to get a key from KBS:
        - Get and replay all event logs, and verify by the measurement register.
        - Generate 2048 bit RSA key pair (a public key and a private key).
        - Encode the public key to base64 for transferring (user_data).
        - Get quote in the TEE with the hash of the public key for measurement (quote).
        - Request wrapped_key and wrapped_swk from KBS with quote and user_data.
        - Decrypt the user key by the SWK.
    """
    def get_key(self, server_url: str, key_id: str) -> bytes: # pylint: disable=too-many-locals
        """Get model key by key ID from the KBS.
  
        This method get and replay all event logs, and verify by the measurement register, then
        construct the request headers and body to request the wrapped_key and wrapped_swk from KBS,
        decrypt the user key by SWK and return the key.

        A example requests and response:
            - request headers:
                Accept:application/json
                Content-Type:application/json
                Attestation-Type:TDX
            - request body:
                {
                    "quote":"",
                    "user_data":""
                }
            - response body:
                {
                    "wrapped_key":"",
                    "wrapped_swk":""
                }

        Args:
            server_url (str): The url of KBS.
            key_id (str): The id of the key.

        Returns:
            bytes: The bytes of the key.
    
        Raises:
            ValueError: If the server_url or key_id is None.
            RuntimeError: If get or verify event log failed, and if get quote or get key failed.
            NotImplementedError: If the subclasses don't implement the method.
        """
        if server_url is None:
            raise ValueError("KBS server url can not be None")
        if key_id is None:
            raise ValueError("KBS key id can not be None")

        # Get and verify event logs before get quote.
        # The exectuion environment judgment will be implemented by ccnp in the future.
        LOG.debug("Getting event log by CCNP")
        event_logs = CcnpSdk.inst().get_cc_eventlog()
        if event_logs is None:
            raise RuntimeError("Get event log failed")
        measurement_dict = CcnpSdk.inst().replay_cc_eventlog(event_logs)
        if verify_event_log(measurement_dict):
            LOG.info("Event log verify successfully.\n")
        else:
            LOG.error("Event log verify failed.\n")
            raise RuntimeError("Event log verify failed.")

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
        pubkey = private_key.public_key()
        pubkey_der = pubkey.public_bytes(encoding=serialization.Encoding.DER,
                                             format=serialization.PublicFormat.SubjectPublicKeyInfo)

        LOG.debug("Getting TDX Quote by CCNP")
        user_data = base64.b64encode(pubkey_der).decode('utf-8')
        quote = CcnpSdk.inst().get_cc_report(data=user_data).dump()
        if quote is None:
            raise RuntimeError("Get TDX Quote failed")
        quote = base64.b64encode(quote.quote).decode('utf-8')

        req_body = {
            "quote": quote,
            "user_data": user_data
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Attestation-Type": "TDX"
        }

        LOG.debug("Getting key from the KBS")
        resp = None
        for _ in range(RETRY_TIMES):
            try:
                resp = requests.post(server_url, json=req_body, headers=headers, verify=False,
                                     timeout=TIMEOUT)
                if resp.status_code in HTTP_OK:
                    break
            except requests.exceptions.ConnectionError:
                LOG.debug("Connect error from the KBS, try again")

        if resp is None or resp.status_code not in HTTP_OK:
            raise RuntimeError("Unexpected response from the KBS")

        resp_body = resp.json()
        if "wrapped_key" not in resp_body or "wrapped_swk" not in resp_body:
            raise RuntimeError("Empty key response from the KBS")

        wrapped_key = base64.b64decode(resp_body['wrapped_key'])
        wrapped_swk = base64.b64decode(resp_body['wrapped_swk'])

        LOG.debug("Decrypting the SWK")
        swk = private_key.decrypt(
          wrapped_swk,
          padding.OAEP(
              mgf=padding.MGF1(algorithm=hashes.SHA256()),
              algorithm=hashes.SHA256(),
              label=None
          )
        )
        return self.decrypt_data(wrapped_key, swk)

    def decrypt_data(self, encrypted_data, key) -> bytes:
        """Decrypt model by a given key.

        Normally, the encrypted data format should be:
         -------------------------------------------------------------------
        | 12 bytes header | [12] bytes IV | encrypted data | [16] bytes tag |
         -------------------------------------------------------------------
        and the 12 bytes header:
         -----------------------------------------------------------
        | uint32 IV length | uint32 tag length | uint32 data length |
         -----------------------------------------------------------

        Args:
            encrypted_data (bytes): The encrypted data for decryption.
            key (bytes): The key for decryption.

        Raises:
            ValueError: If the encrypted_data or key is None.
        """
        if encrypted_data is None:
            raise ValueError("The encrypted data can not be None")
        if key is None:
            raise ValueError("The key can not be None")

        header_len = 12
        iv_len, tag_len, data_len = struct.unpack('<3I', encrypted_data[:header_len])
        iv = encrypted_data[header_len : (iv_len + header_len)]
        data = encrypted_data[(iv_len + header_len) : -tag_len]
        tag = encrypted_data[-tag_len:]

        LOG.debug("Decrypt data, IV len %d, tag len %d, data len %d", iv_len, tag_len, data_len)
        decryptor = Cipher(algorithms.AES(key), modes.GCM(iv, tag)).decryptor()
        decrypted_data = decryptor.update(data) + decryptor.finalize()
        return decrypted_data

# Key broker clients mapping, name can be a KBS short name
KEY_BROKER_HANDLERS = {
    # name: class
    "simple_kbs": SimpleKeyBrokerClient
}
