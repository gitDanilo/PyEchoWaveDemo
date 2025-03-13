from enum import IntEnum
from typing import Optional, Union

MSG_SIZE = 18


class MsgType(IntEnum):
    READY = 0x51
    RX_REQUEST = 0x52
    STOP = 0x53
    TX_REQUEST = 0x54
    REPLY = 0x55
    RX_REPLY = 0x56


class ReplyType(IntEnum):
    OK = 0x0
    BAD_CRC = 0x1
    INVALID_SIZE = 0x2
    INVALID_MSG = 0x3


def calculate_crc8(data: bytes) -> int:
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ 0x07
            else:
                crc <<= 1
        crc &= 0xFF
    return crc


class RcData:
    code: int  # 4 bytes int
    length: int  # 2 bytes int
    repeat: int  # 1 byte int
    # Protocol
    pulse_length: int  # 2 byte int
    sync_factor: int  # 2 byte int
    zero: int  # 2 byte int
    one: int  # 2 byte int
    inverted: bool  # 1 byte bool

    def __init__(
            self,
            code: int,
            length: int,
            repeat: int,
            pulse_length: int,
            sync_factor: int,
            zero: int,
            one: int,
            inverted: bool
    ):
        self.code = code
        self.length = length
        self.repeat = repeat
        self.pulse_length = pulse_length
        self.sync_factor = sync_factor
        self.zero = zero
        self.one = one
        self.inverted = inverted

    @classmethod
    def from_bytes(cls, data: bytes) -> Optional['RcData']:
        if len(data) < 16:  # Minimum size needed for all fields
            return None

        code = int.from_bytes(data[0:4], "little")  # 4 bytes int
        length = int.from_bytes(data[4:6], "little")  # 2 bytes int
        repeat = data[6]  # 1 byte
        pulse_length = int.from_bytes(data[7:9], "little")  # 2 bytes short
        sync_factor = int.from_bytes(data[9:11], "little")  # 2 bytes short
        zero = int.from_bytes(data[11:13], "little")  # 2 bytes short
        one = int.from_bytes(data[13:15], "little")  # 2 bytes short
        inverted = bool(data[15])  # 1 byte boolean

        return cls(
            code=code,
            length=length,
            repeat=repeat,
            pulse_length=pulse_length,
            sync_factor=sync_factor,
            zero=zero,
            one=one,
            inverted=inverted
        )

    def to_bytes(self) -> bytes:
        result = bytearray()
        result.extend(self.code.to_bytes(4, "little"))  # 4 bytes int
        result.extend(self.length.to_bytes(2, "little"))  # 2 bytes int
        result.append(self.repeat)  # 1 byte
        result.extend(self.pulse_length.to_bytes(2, "little"))  # 2 bytes short
        result.extend(self.sync_factor.to_bytes(2, "little"))  # 2 bytes short (2 H/L single byte ints)
        result.extend(self.zero.to_bytes(2, "little"))  # 2 bytes short
        result.extend(self.one.to_bytes(2, "little"))  # 2 bytes short
        result.append(int(self.inverted))  # 1 byte boolean
        return bytes(result)


class ReplyData:
    reply_type: ReplyType  # 1 byte int

    def __init__(self, reply_type: ReplyType):
        self.reply_type = reply_type

    @classmethod
    def from_bytes(cls, data: bytes) -> Optional['ReplyData']:
        if len(data) < 1:
            return None

        reply_type = ReplyType(data[0])  # 1 bytes int
        return cls(reply_type=reply_type)

    def to_bytes(self) -> bytes:
        result = bytearray()
        result.extend(self.reply_type.to_bytes(1, "little"))  # 1 byte int
        return bytes(result)


class Msg:
    msg_type: MsgType  # 1 byte int
    data: Union[RcData, ReplyData, None]
    crc: Optional[int]  # 1 byte int

    def __init__(self, msg_type: MsgType, data: Union[RcData, ReplyData, None] = None, crc: Optional[int] = None):
        self.msg_type = msg_type
        self.data = data
        self.crc = crc

    @classmethod
    def from_bytes(cls, data: bytes) -> Optional['Msg']:
        if len(data) < MSG_SIZE:
            return None

        msg_type = MsgType(data[0])
        crc = int.from_bytes(data[-1:], "little")

        if msg_type == MsgType.TX_REQUEST or msg_type == MsgType.RX_REPLY:
            rc_data = RcData.from_bytes(data[1:-1])
            return cls(msg_type=msg_type, data=rc_data, crc=crc) if rc_data is not None else None

        if msg_type == MsgType.REPLY:
            reply_data = ReplyData.from_bytes(data[1:-1])
            return cls(msg_type=msg_type, data=reply_data, crc=crc) if reply_data is not None else None

        return cls(msg_type=msg_type, data=None, crc=crc)

    def to_bytes(self) -> bytes:
        result = bytearray()
        result.append(self.msg_type)  # 1 byte for msg_type

        if self.data is not None:
            result.extend(self.data.to_bytes())  # Add RcData bytes

        # Pad with zeros if needed to maintain MSG_SIZE
        while len(result) < MSG_SIZE - 1:  # -1 for CRC byte
            result.append(0)

        # Calculate CRC
        if self.crc is None:
            self.crc = calculate_crc8(result)

        result.append(self.crc)  # 1 byte for CRC
        return bytes(result)
