import hashlib
import math
import string
import sys

from fastfpe import ff3_1

RADIX_MAX = 256
DOMAIN_MIN = 1_000_000  # 1M required in FF3-1


def check_digit(value: str) -> str:
    # we only need to check against random strings being decrypted, not common
    # manual entry errors
    return str((10 - (sum(map(int, value)) % 10)) % 10)


class InvalidID(ValueError):
    pass


class TurbIDCipher:
    """
    A class that represents a TurbID cipher for encrypting and decrypting integer IDs.

    Args:
        key (str): The encryption key.
        tweak (str): The tweak value used for encryption.
        length (int, optional): The length of the encrypted ID. Defaults to 24.
        alphabet (str, optional): The alphabet used for encoding the ID. Defaults to digits and ASCII letters.
        key_length (int, optional): The length of the encryption key in bits. Must be 128, 192, or 256. Defaults to 128.

    Raises:
        ValueError: If the alphabet is not between 2 and 95 ASCII characters.
        ValueError: If the length is not within the valid range for the given alphabet.
        ValueError: If the key length is not 128, 192, or 256 bits.

    Attributes:
        min_len (int): The minimum length of the encrypted ID based on the given alphabet.
        max_len (int): The maximum length of the encrypted ID based on the given alphabet.
        key_length (int): The length of the encryption key in bits.
        length (int): The length of the encrypted ID.
        alphabet (str): The alphabet used for encoding the ID.
        tweak (str): The tweak value used for encryption.

    Methods:
        encrypt(int_id: int) -> str: Encrypts an integer ID and returns the encrypted string.
        decrypt(str_id: str) -> int: Decrypts a string ID and returns the original integer ID.
    """

    def __init__(
        self,
        key: str,
        tweak: str,
        length: int = 24,
        alphabet: str = string.digits + string.ascii_letters,
        key_length: int = 128,
    ):
        radix = len(alphabet)
        if radix < 2 or radix > RADIX_MAX:
            raise ValueError(f"The alphabet must be between 2 and {RADIX_MAX} ASCII characters")

        if len(set(alphabet)) != len(alphabet):
            raise ValueError("The alphabet must not contain duplicate characters")

        if not all(c in string.printable for c in alphabet):
            raise ValueError("The alphabet must contain only printable ASCII characters")

        if not all(c in alphabet for c in string.digits):
            raise ValueError("The alphabet must contain all digits")

        self.min_len = math.ceil(math.log(DOMAIN_MIN) / math.log(radix))
        self.max_len = 2 * math.floor(96 / math.log2(radix))

        if length < self.min_len or length > self.max_len:
            raise ValueError(
                f"With the given alphabet, ids are limited to a length between {self.min_len} and {self.max_len}, inclusive"
            )

        if key_length not in (128, 192, 256):
            raise ValueError("The key length must be 128, 192, or 256 bits")

        self.key_length = key_length

        self.length = length
        self.alphabet = alphabet
        self.tweak = tweak

        # ff3-1 expects a 32-byte key, so hash the provided key to the specified
        # key length
        self.keyhash = hashlib.blake2b(key.encode(), digest_size=self.key_length // 8).hexdigest()

        # ff3-1 expects a 7 bytes tweak, so we use blake2b to get a 7-byte hash.
        #
        # Under normal circumstances the tweak should be unique for each
        # operation, so the same plaintext will encrypt to different ciphertexts
        # each time, but in our case we want the same plaintext to encrypt to
        # the same ciphertext each time, so we use a fixed tweak
        self._tweak = hashlib.blake2b(self.tweak.encode(), digest_size=7).hexdigest()

        # self._ff3 = #FF3Cipher.withCustomAlphabet(keyhash, self._tweak, self.alphabet)

    def _add_check_digit(self, int_as_str: str) -> str:
        # Decrypting a random string, tampered ID, or ID created with a
        # different key or tweak can sometimes result in a string that is all
        # digits. We add a check digit to the original int to catch it.
        return f"{int_as_str}{check_digit(int_as_str)}"

    def _verify_check_digit(self, int_as_str: str) -> str:
        if not int_as_str.isdigit():
            raise InvalidID("ID corrupted or invalid.")

        value, cd = int_as_str[:-1], int_as_str[-1]
        if check_digit(value) != cd:
            raise InvalidID("ID corrupted or invalid.")

        return value

    def encrypt(self, int_id: int) -> str:
        """
        Encrypts an integer ID and returns the encrypted string.

        Args:
            int_id (int): The integer ID to encrypt.

        Returns:
            str: The encrypted string.

        Raises:
            InvalidID: If the ID is too long for the specified length.
        """
        if int_id > sys.maxsize:
            raise InvalidID("ID is too large to encrypt.")

        as_str = str(int_id)
        # we need 1 digit for the check digit
        if len(as_str) - 1 > self.length:
            raise InvalidID("ID is too long to encrypt.")

        # after adding the check digit, we pad the int with zeros to the length
        # so the FPE cipher outputs a string of the expected length
        return ff3_1.encrypt(
            self.keyhash,
            self._tweak,
            self.alphabet,
            self._add_check_digit(as_str).zfill(self.length),
        )

    def decrypt(self, str_id: str) -> int:
        """
        Decrypts a string ID and returns the original integer ID.

        Args:
            str_id (str): The string ID to decrypt.

        Returns:
            int: The original integer ID.

        Raises:
            InvalidID: If the ID length does not match the expected length.
            InvalidID: If the decrypted value is not a number.
        """
        id_length = len(str_id)
        if id_length != self.length:
            raise InvalidID("ID length does not match the expected length.")

        decrypted_value = ff3_1.decrypt(self.keyhash, self._tweak, self.alphabet, str_id)

        # self._ff3.decrypt(str_id)

        return int(self._verify_check_digit(decrypted_value))
