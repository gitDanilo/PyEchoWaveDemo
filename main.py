from time import sleep
from typing import List

import serial

from protocol import Msg, MsgType, RcData, ReplyData, MSG_SIZE, ReplyType


def main():
    print("EchoWaveDemo")
    port = serial.Serial("COM7", 9600, bytesize=8, parity='N', stopbits=1)

    ret = port.read(MSG_SIZE)
    msg = Msg.from_bytes(ret)
    if msg is not None and msg.msg_type == MsgType.READY:
        print(f"received ready msg")

    # request codes
    print("sending rx request...")
    rx_request = Msg(msg_type=MsgType.RX_REQUEST)
    port.write(rx_request.to_bytes())
    port.flush()

    # check for reply
    ret = port.read(MSG_SIZE)
    msg = Msg.from_bytes(ret)
    if msg is not None and isinstance(msg.data, ReplyData):
        print(f"reply received: 0x{msg.data.reply_type:X}")

    # read 3 codes
    print("listening for codes...")
    codes: List[RcData] = []
    for i in range(0, 6):
        ret = port.read(MSG_SIZE)
        msg = Msg.from_bytes(ret)
        if msg is not None and isinstance(msg.data, RcData):
            print(f"code received: 0x{msg.data.code:X}")
            codes.append(msg.data)

        # acknowledge
        ok_reply = Msg(msg_type=MsgType.REPLY, data=ReplyData(reply_type=ReplyType.OK))
        port.write(ok_reply.to_bytes())
        port.flush()

    # send stop command
    print("suspending code transmission...")
    stop = Msg(msg_type=MsgType.STOP)
    port.write(stop.to_bytes())
    port.flush()

    ret = port.read(MSG_SIZE)
    msg = Msg.from_bytes(ret)
    if msg is not None and isinstance(msg.data, ReplyData):
        print(f"reply received: 0x{msg.data.reply_type:X}")

    input("press enter to send last code...")

    # send tx request
    print("sending last tx request...")
    last_code = codes[-1]
    last_code.repeat = 4
    tx_request = Msg(msg_type=MsgType.TX_REQUEST, data=last_code)
    port.write(tx_request.to_bytes())
    port.flush()

    ret = port.read(MSG_SIZE)
    msg = Msg.from_bytes(ret)
    if msg is not None and isinstance(msg.data, ReplyData):
        print(f"reply received: 0x{msg.data.reply_type:X}")

    print("exiting...")

    port.close()


if __name__ == '__main__':
    main()
