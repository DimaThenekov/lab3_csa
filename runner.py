#!/usr/bin/python3
import logging
import sys


class MemoryManager:
    """
        Data Memory
         ```
        MAG(A,B) =>
            if B==1:
                return 0b11111111_11111111_11111111_11111111
            if B==2:
                if A==0:
                    return 0b11111111_11111111
                if A==1:
                    return 0b11111111_11111111_00000000_00000000
            if B==4
                if A==0:
                    return 0b11111111
                if A==1:
                    return 0b11111111_00000000
                if A==2:
                    return 0b11111111_00000000_00000000
                if A==3:
                    return 0b11111111_00000000_00000000_00000000
        MAG2(A,B) =>
            if B==1:
                return 0
            if B==2:
                if A==0:
                    return 0
                if A==1:
                    return 16
            if B==4
                if A==0:
                    return 0
                if A==1:
                    return 8
                if A==2:
                    return 16
                if A==3:
                    return 24


                    |       |         ^
                    |value  |address  |data_out
                    |       |         |
                    |       |         |
                    |       |       +----+  +---------+
                    |       |       |A>>C|<-|MAG2(A,B)|
                    |       |       +----+  +---------+
                    |       |         ^
                    |       |      +-------+  +--------+
                    |       |      |A AND C|<-|MAG(A,B)|
                    |       |      +-------+  +--------+
                    |       |         ^  +-----+                                              +--------+
                +---|-------|---------|->|MUX_D|<---------------------------------------------| out    |
                |   |       |         |  +-----+                                              |        |
                |   |       |         |   |                                                   |        |
    +-------+   |   |       |         |   v                                                   |        |
    |       |   |   |       |    +----------+                        +-------------+  +----+  | data   |
    | malloc|   |   |       |    |   DATA   |+--------------------A->| A AND NOT B |->|    |  | memory |
    |       |   |   |       |    +----------+                        +-------------+  |    |  |        |
    |       v   |   |       |                                            ^            |    |  |        |
    | +----------+  |       |                                     +----B-+            | OR |->| inp    |
    | | MEM_SIZE |  |       |                                     |      v            |    |  |        |
    | +----------+  |       |                            +------+ |  +---------+      |    |  |        |
    |       |       +-------|-------------------------A->| A<<C |-|->| A AND B |----->|    |  |        |
    |       |       |       |                            +------+ |  +---------+      +----+  |        |
    |       |       |       |                                ^    |                           |        |
    |       |       |       |                                C    |                           |        |
    |       |       |       |                                |    |                           |        |
    |       |       |       |                       +----------+  |                           |        |
    |       |       |       |                +---A->| MAG2(A,B)|  |                           |        |
    |       |       |       |                |      +----------+  |                           |        |
    |       |       |       |     +---  ---+ |           ^        |                           |        |
    |       |       |       +---->|A  \/MOD|-+ +-------B-+        |                        wr |        |
    |       v       v             +        + | |         v        |                       --->|        |
    |     +---\   /---+            \      /  | |    +----------+  |                           |        |
    |     \    \_/    /             | A/B|   +-|-A->| MAG(A,B) |--+                        oe |        |
    |      \   ADD   /             /      \    |    +----------+                          --->|        |
    |       \_______/             +        +   |                                              |        |
    |           |              +->|B  /\DIV|---|--------------------------------------------->|address |
    |           |              |  +---  ---+   |                                              +--------+
    |           |              |               |
    +-----------+           +-----+            |
                            | MOD |------------+
                            +-----+
                               ^
                               | adress mod
                               |
                   1-32bit 2-16bit 4-8bit
         ```
    """

    def __init__(self):
        self.memory = []
        self.mod = 1

    def malloc(self, count_of_int32):
        assert count_of_int32 > 0, "count_of_int32<=0"
        address = len(self.memory)
        self.memory.extend([0] * count_of_int32)
        return address

    def set_mod(self, mod):
        assert mod in [1, 2, 4]
        self.mod = mod

    def setmem(self, address, value):
        assert address // self.mod < len(self.memory)
        self.memory[address // self.mod] = self._set_word(
            self.memory[address // self.mod], value, address % self.mod, self.mod
        )

    def _set_word(self, int32, word, select_word, word_size):
        MAG = 0b11111111_11111111_11111111_11111111
        MAG2 = 32
        start_word = 0
        if word_size == 2:
            MAG = 0b11111111_11111111
            MAG2 = 16
            start_word = (1 - select_word) * MAG2
        elif word_size == 4:
            MAG = 0b11111111
            MAG2 = 8
            start_word = (3 - select_word) * MAG2
        mask = MAG << start_word
        masked_int32 = int32 & ~mask
        new_word = word & MAG
        new_word = new_word << start_word
        return masked_int32 | new_word

    def _get_word(self, int32, select_word, word_size):
        MAG = 0b11111111_11111111_11111111_11111111
        MAG2 = 32
        start_word = 0
        if word_size == 2:
            MAG = 0b11111111_11111111
            MAG2 = 16
            start_word = (1 - select_word) * MAG2
        elif word_size == 4:
            MAG = 0b11111111
            MAG2 = 8
            start_word = (3 - select_word) * MAG2
        return (int32 >> start_word) & MAG

    def getmem(self, address):
        return self._get_word(self.memory[address // self.mod], address % self.mod, self.mod)


mm = MemoryManager()
error_list = []


def crop_int_to_int32(num):
    max_int32 = 2**31 - 1
    min_int32 = -(2**31)
    cropped_num = num & 0xFFFFFFFF
    if cropped_num & 0x80000000:
        return -(0x100000000 - cropped_num) if cropped_num > max_int32 else cropped_num
    else:
        return cropped_num


def crop_int_to_int16(num):
    max_int32 = 2**15 - 1
    min_int32 = -(2**15)
    cropped_num = num & 0xFFFF
    if cropped_num & 0x8000:
        return -(0x10000 - cropped_num) if cropped_num > max_int32 else cropped_num
    else:
        return cropped_num


def crop_int_to_uint16(num):
    max_uint16 = 2**16 - 1
    min_uint16 = 0
    cropped_num = num & 0xFFFF
    return min(max_uint16, max(min_uint16, cropped_num))


programm = []


def load_program(mm, file_name):
    def A(REG):
        return ["AL", "AX", "EAX"].index(REG) * 0b00000100_00000000_00000000_00000000

    def F(NUM):
        #            000     001      010       011         100        101         110        111
        # F(ARG) ::= NUM || [NUM] || EAX+NUM || [EAX+NUM] ||  IP+NUM || [IP+NUM] ||  SP+NUM || [SP+NUM]
        NUM = NUM.strip()
        in_mem = 1 if "[" in NUM else 0
        if in_mem == 1:
            NUM = NUM[1:-1]
        value = 0
        if NUM.replace("+", " ").replace("-", " ").split(" ")[-1].isdigit():
            value = (1 if NUM.count("-") % 2 == 0 else -1) * int(NUM.replace("+", " ").replace("-", " ").split(" ")[-1])
        if NUM.isdigit():
            return in_mem * 0b1_00000000_00000000 + crop_int_to_uint16(value)
        REG = NUM.replace("+", " ").replace("-", " ").split(" ")[0]
        return (["", "EAX", "IP", "SP"].index(REG) * 2 + in_mem) * 0b1_00000000_00000000 + crop_int_to_uint16(value)

    def compile_programm(ptr, programm):
        for i in range(len(programm)):
            cmd = programm[i].split("#")[0].strip().replace(",", " ").replace("  ", " ").replace("  ", " ").split(" ")
            # print(cmd)
            if cmd[0] == "NOP":
                mm.setmem(ptr + i, 0b00000000_00000000_00000000_00000000)
            elif cmd[0] == "HALT":
                mm.setmem(ptr + i, 0b00010000_00000000_00000000_00000000)
            elif cmd[0] == "MOV":
                if cmd[1] in ("AL", "AX", "EAX"):
                    mm.setmem(ptr + i, 0b00100000_00000000_00000000_00000000 + A(cmd[1]) + F(cmd[2]))
                else:
                    mm.setmem(ptr + i, 0b00110000_00000000_00000000_00000000 + A(cmd[2]) + F(cmd[1][1:-1]))
            elif cmd[0] == "WORD32":
                mm.setmem(ptr + i, crop_int_to_int32(int(cmd[1])))
            elif cmd[0] in ("ADC", "ADD", "SBC", "SUB", "OR", "XOR", "AND", "MUL", "SHR", "SHL", "CMP", "MOD"):
                mm.setmem(
                    ptr + i,
                    0b01000000_00000000_00000000_00000000
                    + (
                        ["ADC", "ADD", "SBC", "SUB", "OR", "XOR", "AND", "MUL", "SHR", "SHL", "CMP", "MOD"].index(
                            cmd[0]
                        )
                        << 20
                    )
                    + A("EAX")
                    + F(cmd[1]),
                )
            elif cmd[0] in ("NOT", "NEG", "RCL", "RCR", "ZEXT8", "ZEXT16", "EXT8", "EXT16"):
                mm.setmem(
                    ptr + i,
                    0b01010000_00000000_00000000_00000000
                    + (["NOT", "NEG", "RCL", "RCR", "ZEXT8", "ZEXT16", "EXT8", "EXT16"].index(cmd[0]) << 20),
                )
            elif cmd[0] in ("OUT", "IN", "MALLOC32", "MALLOC16", "MALLOC8"):
                mm.setmem(
                    ptr + i,
                    0b01100000_00000000_00000000_00000000
                    + (["OUT", "IN", "MALLOC32", "MALLOC16", "MALLOC8"].index(cmd[0]) << 16),
                )
            elif cmd[0] == "INT" and cmd[1] in ("OUT", "IN", "MALLOC32", "MALLOC16", "MALLOC8"):
                mm.setmem(
                    ptr + i,
                    0b01100000_00000000_00000000_00000000
                    + (["OUT", "IN", "MALLOC32", "MALLOC16", "MALLOC8"].index(cmd[1]) << 16),
                )
            elif cmd[0] == "CALL" and cmd[1] in ["A", "E", "NE", "G", "L", "GE", "LE"]:
                mm.setmem(
                    ptr + i,
                    0b10000000_00000000_00000000_00000000
                    + (["A", "E", "NE", "G", "L", "GE", "LE"].index(cmd[1]) << 20)
                    + F(cmd[2]),
                )
            elif cmd[0] == "CALL":
                mm.setmem(ptr + i, 0b10000000_00000000_00000000_00000000 + F(cmd[1]))
            elif cmd[0] == "RET":
                mm.setmem(ptr + i, 0b10010000_00000000_00000000_00000000)
            elif cmd[0] == "JMP" and cmd[1] in ["A", "E", "NE", "G", "L", "GE", "LE"]:
                mm.setmem(
                    ptr + i,
                    0b10100000_00000000_00000000_00000000
                    + (["A", "E", "NE", "G", "L", "GE", "LE"].index(cmd[1]) << 20)
                    + F(cmd[2]),
                )
            elif cmd[0] == "JMP":
                mm.setmem(ptr + i, 0b10100000_00000000_00000000_00000000 + F(cmd[1]))
            elif cmd[0] == "PUSH":
                mm.setmem(ptr + i, 0b10110000_00000000_00000000_00000000 + F(cmd[1]))
            elif cmd[0] == "POP":
                mm.setmem(ptr + i, 0b11000000_00000000_00000000_00000000)
            elif cmd[0] == "SWAP":
                mm.setmem(ptr + i, 0b11010000_00000000_00000000_00000000 + F(cmd[1][1:-1]))
            else:
                error_list.append("undefined command: " + " ".join(cmd))

    import json

    with open(file_name) as f:
        global programm
        programm = json.load(f)
        ptr = mm.malloc(len(programm))
        compile_programm(ptr, programm)
        # for i in range(0,len(programm)):
        #    print('at '+str(ptr+i)+' with command "'+programm[i]+'" value is '+str(mm.getmem(ptr+i)))


class magic_numbers:
    MUX_A_ALU = 0
    MUX_A_INP = 1

    MUX_L_AC = 0
    MUX_L_AR = 1
    MUX_L_0 = 2

    MUX_R_DR = 0
    MUX_R_1 = 1
    MUX_R_SP = 2
    MUX_R_IP = 3

    MUX_S_INC = 0
    MUX_S_DEC = 1

    MUX_DM_MOD_1 = 0
    MUX_DM_MOD_2 = 1
    MUX_DM_MOD_4 = 2


class DataPath:
    """

     ```
     ! Каждый MUX имеет селектор, но ради упрощения схемы они не отображены

                         ^
                         |32bit (instruction)
                         |
     +----+--------------+--------------+
     |    |              |              |
     |    |  |           |              |
     |    |  | inp    _Z_C_S_           |
     |    v  v       /   OF  \  alu_op  |
     | +-------+    /   ___   \<------  |
     | | MUX_A |   /   /   \   \        |
     | +-------+  +---/     \---+       |
     |    |         ^         ^         |
     |    |latch_ac |         |         |latch_ip
     |    v         |         |         v
     | +----+   +-------+ +-------+   +----+
     | | AC |-->| MUX_L | | MUX_R |<--| IP |
     | +----+   +-------+ +-------+   +----+
     |     |     ^     ^   ^  ^  ^
     | out |     |     |   |  |  |
     |     v     |    (0)  | (1) +---------------+----+
     |           |         |     |               |    |
     |           |         |     |             (+1)  (-1)
     |           |         |     |               |    |
     |           |         |     |               v    v
     |latch_ar+----+    +----+ +----+ latch_sp +-------+
     +------->| AR |    | DR | | SP |<---------| MUX_S |
     |        +----+    +----+ +----+          +-------+
     |           |         ^
     |           |         |           |    |    |
     |value      |address  |data_out   |wr  |oe  |malloc
     v           v         |           v    v    v
    +---------------------------------------------------+
    |  data                                             |
    |  memory                                           |
    +---------------------------------------------------+
                       ^
                       | adress mod
                       |
                 +-------------+
                 | MUX_DM_MOD  |
                 +-------------+
                     ^  ^  ^
                     |  |  |
                     |  |  |
                     1  2  4
    ```

    - data_memory -- однопортовая, поэтому либо читаем, либо пишем.

    - input/output -- токенизированная логика ввода-вывода. Не детализируется в
      рамках модели.

    - input -- чтение может вызвать остановку процесса моделирования, если буфер
      входных значений закончился.

    - malloc -- операция над памятью добавляющая n нулевых машинных слов в конец.

    Реализованные методы соответствуют сигналам защёлкивания значений:

    - `signal_latch_ip` -- защёлкивание адреса следующей выполняемой команды
    - `signal_latch_ac` -- защёлкивание аккумулятора
    - `signal_latch_ar` -- защёлкивание адреса в памяти
    - `signal_latch_sp` -- защёлкивание адреса вершины стека
    - `signal_oe` -- чтение из память
    - `signal_wr` -- запись в память
    - `signal_malloc` -- выделение памяти
    - `signal_out` -- вывод в порт.
    - `signal_adress_mod` -- устанавливает режим адресации.

    Сигнал "исполняется" за один такт. Корректность использования сигналов --
    задача `ControlUnit`.
    """

    memory_manager = None
    rAC = None
    rAR = None
    rSP = None
    rIP = None
    rDR = None
    alu_flags = None
    input_buffer = None
    output_buffer = None

    def __init__(self, memory_manager, input_buffer):
        self.memory_manager = memory_manager
        self.rAC = 0
        self.rAR = 0
        self.rSP = 0
        self.rIP = 0
        self.rDR = 0
        self.alu_flags = {"OF": False, "C": False, "Z": True, "S": False}
        self.input_buffer = input_buffer
        self.output_buffer = []

    def signal_latch_ip(self, sel_l, sel_r, alu_op):
        self.rIP = self.alu(sel_l, sel_r, alu_op)

    def signal_latch_ac(self, sel_l, sel_r, alu_op, sel_a=magic_numbers.MUX_A_ALU):
        if sel_a == magic_numbers.MUX_A_INP:
            self.rAC = self.input_buffer.pop(0)
        else:
            self.rAC = self.alu(sel_l, sel_r, alu_op)

    def signal_latch_ar(self, sel_l, sel_r, alu_op):
        self.rAR = self.alu(sel_l, sel_r, alu_op)

    def signal_latch_sp(self, sel_s):
        if sel_s == magic_numbers.MUX_S_INC:
            self.rSP += 1
        else:
            self.rSP -= 1

    def signal_oe(self):
        self.rDR = self.memory_manager.getmem(self.rAR)

    def signal_wr(self, sel_l, sel_r, alu_op):
        self.memory_manager.setmem(self.rAR, self.alu(sel_l, sel_r, alu_op))

    def signal_malloc(self, sel_l, sel_r, alu_op):
        self.rDR = self.memory_manager.malloc(self.alu(sel_l, sel_r, alu_op))

    def signal_adress_mod(self, sel_dm):
        if sel_dm == magic_numbers.MUX_DM_MOD_1:
            self.memory_manager.set_mod(1)
        elif sel_dm == magic_numbers.MUX_DM_MOD_2:
            self.memory_manager.set_mod(2)
        elif sel_dm == magic_numbers.MUX_DM_MOD_4:
            self.memory_manager.set_mod(4)

    def signal_out(self):
        symbol = chr(self.rAC)
        self.output_buffer.append(symbol)

    def overflow(self):
        return self.alu_flags["OF"]

    def carry(self):
        return self.alu_flags["C"]

    def zero(self):
        return self.alu_flags["Z"]

    def sign(self):
        return self.alu_flags["S"]

    def alu(self, sel_l, sel_r, alu_op):
        left_value = 0
        right_value = 1
        if sel_l == magic_numbers.MUX_L_AC:
            left_value = self.rAC
        elif sel_l == magic_numbers.MUX_L_AR:
            left_value = self.rAR

        if sel_r == magic_numbers.MUX_R_DR:
            right_value = self.rDR
        elif sel_r == magic_numbers.MUX_R_SP:
            right_value = self.rSP
        elif sel_r == magic_numbers.MUX_R_IP:
            right_value = self.rIP

        if "crop_right_to_int16" in alu_op and alu_op["crop_right_to_int16"]:
            right_value = crop_int_to_int16(right_value)

        out_value = 0
        if alu_op["op"] == "ADC":
            out_value = left_value + right_value + int(self.alu_flags["C"])
        elif alu_op["op"] == "ADD":
            out_value = left_value + right_value
        elif alu_op["op"] == "SBC":
            out_value = left_value - right_value - int(self.alu_flags["C"])
        elif alu_op["op"] == "SUB":
            out_value = left_value - right_value
        elif alu_op["op"] == "OR":
            out_value = left_value | right_value
        elif alu_op["op"] == "XOR":
            out_value = left_value ^ right_value
        elif alu_op["op"] == "AND":
            out_value = left_value & right_value
        elif alu_op["op"] == "MUL":
            out_value = left_value * right_value
        elif alu_op["op"] == "SHR":
            out_value = left_value >> right_value
        elif alu_op["op"] == "SHL":
            out_value = left_value << right_value
        elif alu_op["op"] == "CMP":
            out_value = left_value - right_value
        elif alu_op["op"] == "MOD":
            out_value = left_value % right_value
        else:
            raise "E453"
        if "ceil_div_2" in alu_op and alu_op["ceil_div_2"]:
            out_value = (1 + out_value) >> 1
        if "ceil_div_4" in alu_op and alu_op["ceil_div_4"]:
            out_value = (3 + out_value) >> 2
        if "unceil_div_2" in alu_op and alu_op["unceil_div_2"]:
            out_value = out_value << 1
        if "unceil_div_4" in alu_op and alu_op["unceil_div_4"]:
            out_value = out_value << 2
        if "set_flag" in alu_op:
            self.alu_flags["Z"] = out_value == 0
            self.alu_flags["S"] = out_value < 0
            if alu_op["op"] in ("ADC", "ADD", "SBC", "SUB", "CMP"):
                self.alu_flags["OF"] = crop_int_to_int32(out_value) != out_value
                if alu_op["op"] == "ADC":
                    self.alu_flags["C"] = (left_value & 0xFFFFFFFF) + (right_value & 0xFFFFFFFF) + int(
                        self.alu_flags["C"]
                    ) > 0xFFFFFFFF
                if alu_op["op"] == "ADD":
                    self.alu_flags["C"] = (left_value & 0xFFFFFFFF) + (right_value & 0xFFFFFFFF) > 0xFFFFFFFF
                if alu_op["op"] == "SBC":
                    self.alu_flags["C"] = (left_value & 0xFFFFFFFF) + (right_value & 0xFFFFFFFF) + int(
                        self.alu_flags["C"]
                    ) < 0
                if alu_op["op"] in ("SUB", "CMP"):
                    self.alu_flags["C"] = (left_value & 0xFFFFFFFF) + (right_value & 0xFFFFFFFF) < 0
        if alu_op["op"] == "CMP":
            return left_value
        else:
            return crop_int_to_int32(out_value)


# CPU registers:
# EAX (16bit: AX, 8bit: AL) - 32-bit ACCUMULATOR. General purpose register
# SP - 32-bit STACK POINTER
# IP - 32-bit INSTRUCTION POINTER
# CPU 4 flags: OF - overflow, C - carry, Z - zero, S - sign

# MEM(32 bit address) = 32bit value by address
#            000      001        010         011          100         101          110         111
# F(ARG) ::= ARG || MEM(ARG) || A+ARG || MEM(A+ARG) ||  IP+ARG || MEM(IP+ARG) ||  SP+ARG || MEM(SP+ARG)

# A ::= AL || AX || EAX || RESERVED_FOR_x64

# 0000xxxx.xxxxxxxx.xxxxxxxx.xxxxxxxx NOP            NOP
# 0001xxxx.xxxxxxxx.xxxxxxxx.xxxxxxxx HALT           HALT

# 0010RRxx.xxxxxFFF.AAAAAAAA.AAAAAAAA MOV            A := F(ARG)            Z S
# MOV AL, -10
# MOV AL, [A-2]
# MOV AL, [IP+2]
# MOV AL, SP
# 0011RRxx.xxxxxFFF.AAAAAAAA.AAAAAAAA MOV            MEM(F(ARG)) := A
# MOV [10], AH
# MOV [SP+10], AL
# MOV [[IP-1]], EAX

# OP ::= ADC || ADD || SBC || SUB || OR || XOR || AND || MUL || SHR || SHL || CMP
# 0100RRxx.OPERxFFF.AAAAAAAA.AAAAAAAA ALU OP ARG                             OF C Z S
# ALU ADC AL [IP+2]
# ALU ADD EAX -10

# UOP ::= NOT || NEG || RCL || RCR || ZEXT8 || ZEXT16 || EXT8 || EXT16
# 0101xxxx.OPERxxxx.xxxxxxxx.xxxxxxxx ALU UOP                                OF C Z S
# ALU NOT
# ALU RCR

# 0110xxxx.00000001.xxxxxxxx.xxxxxxxx OUT         WRITE(AL)
# 0110xxxx.00000010.xxxxxxxx.xxxxxxxx IN          AL := READ()
# 0110xxxx.00000011.xxxxxxxx.xxxxxxxx MALLOC32    EAX := MALLOC(EAX)
# 0110xxxx.00000100.xxxxxxxx.xxxxxxxx MALLOC16    EAX := MALLOC((1+EAX)>>1)
# 0110xxxx.00000101.xxxxxxxx.xxxxxxxx MALLOC8     EAX := MALLOC((3+EAX)>>2)

# COND = {
#   A: 0000  # always
#   E: 0001  # = (Z = 1)
#   NE: 0010  # != (Z = 0)
#   G: 0011  # > ((S xor OF) or Z = 0)
#   L: 0100  # < (S xor OF = 1)
#   GE: 0101  # >= (S xor OF = 0)
#   LE: 0110  # <= ((S xor OF) or Z = 1)
# }
# 1000xxxx.CONDxFFF.AAAAAAAA.AAAAAAAA CALL        MEM(++SP) = IP; IP = F(ARG)
# 1001xxxx.xxxxxxxx.xxxxxxxx.xxxxxxxx RET         IP = MEM(SP--)
# 1010xxxx.CONDxFFF.AAAAAAAA.AAAAAAAA JUMP        IP = F(ARG)
# 1011xxxx.xxxxxFFF.AAAAAAAA.AAAAAAAA PUSH        MEM(++SP) = F(ARG)
# 1100xxxx.xxxxxxxx.xxxxxxxx.xxxxxxxx POP         F(ARG) = MEM(SP--)            Z S
# 1101RRxx.xxxxxFFF.AAAAAAAA.AAAAAAAA SWAP        B=A; A=MEM(F(ARG)); MEM(F(ARG))=B            Z S
# SWAP [SP]


class ControlUnit:
    """Блок управления процессора. Выполняет декодирование инструкций и
    управляет состоянием модели процессора, включая обработку данных (DataPath).

    Согласно варианту, любая инструкция может быть закодирована в одно слово.
    Следовательно, индекс памяти команд эквивалентен номеру инструкции.

    ```text
                                   +-------------+
                            +------| instruction |
                            |      |   decoder   |
                            |      |             |<-------+
                            |      +-------------+        |
                            |              ^              |
                            |signals       | instruction  |
                            |              |              |
                            |        +----------+  flags  |
                            +------->|          |---------+
                                     | DataPath |
                      input -------->|          |----------> output
                                     +----------+
    ```

    """

    data_path = None
    step_counter = None
    _tick = None

    def __init__(self, data_path):
        self.data_path = data_path
        self.step_counter = 0
        self._tick = 0

    def tick(self, n=1):
        self._tick += n

    def current_tick(self):
        return self._tick

    def execute_instruction(self, instr, data):
        # print(data)
        if instr == 0:  # NOP
            return
        elif instr == 1:  # HALT
            raise "STOP"
        elif instr == 2:  # MOV A 5
            if data["RR"] != 2:
                self.tick()
                self.data_path.signal_adress_mod(
                    {0: magic_numbers.MUX_DM_MOD_4, 1: magic_numbers.MUX_DM_MOD_2}[data["RR"]]
                )
            if data["F"] == 0:  # MOV A 5
                self.tick()
                self.data_path.signal_latch_ac(
                    magic_numbers.MUX_L_0, magic_numbers.MUX_R_DR, {"op": "ADD", "crop_right_to_int16": True}
                )
            elif data["F"] == 1:  # MOV A [5]
                self.tick(3)
                self.data_path.signal_latch_ar(
                    magic_numbers.MUX_L_0, magic_numbers.MUX_R_DR, {"op": "ADD", "crop_right_to_int16": True}
                )
                self.data_path.signal_oe()
                self.data_path.signal_latch_ac(magic_numbers.MUX_L_0, magic_numbers.MUX_R_DR, {"op": "ADD"})
            elif data["F"] == 2:  # MOV A A+5
                self.tick()
                self.data_path.signal_latch_ac(
                    magic_numbers.MUX_L_AC, magic_numbers.MUX_R_DR, {"op": "ADD", "crop_right_to_int16": True}
                )
            elif data["F"] == 3:  # MOV A [A+5]
                self.tick(3)
                self.data_path.signal_latch_ar(
                    magic_numbers.MUX_L_AC, magic_numbers.MUX_R_DR, {"op": "ADD", "crop_right_to_int16": True}
                )
                self.data_path.signal_oe()
                self.data_path.signal_latch_ac(magic_numbers.MUX_L_0, magic_numbers.MUX_R_DR, {"op": "ADD"})
            elif data["F"] == 4:  # MOV A IP+5
                raise "E594"
            elif data["F"] == 5:  # MOV A [IP+5]
                raise "E596"
            elif data["F"] == 6:  # MOV A SP+5
                raise "E602"
            elif data["F"] == 7:  # MOV A [SP+5]
                if data["RR"] != 2:
                    raise "E601"
                self.tick(4)
                self.data_path.signal_latch_ar(magic_numbers.MUX_L_0, magic_numbers.MUX_R_SP, {"op": "ADD"})
                self.data_path.signal_latch_ar(
                    magic_numbers.MUX_L_AR, magic_numbers.MUX_R_DR, {"op": "ADD", "crop_right_to_int16": True}
                )
                self.data_path.signal_oe()
                self.data_path.signal_latch_ac(magic_numbers.MUX_L_0, magic_numbers.MUX_R_DR, {"op": "ADD"})

            if data["RR"] != 2:
                self.tick()
                self.data_path.signal_adress_mod(magic_numbers.MUX_DM_MOD_1)
        elif instr == 3:  # MOV [5] A
            if data["F"] == 0:  # MOV [5] A
                self.tick(2)
                self.data_path.signal_latch_ar(
                    magic_numbers.MUX_L_0, magic_numbers.MUX_R_DR, {"op": "ADD", "crop_right_to_int16": True}
                )
                if data["RR"] != 2:
                    self.data_path.signal_adress_mod(
                        {0: magic_numbers.MUX_DM_MOD_4, 1: magic_numbers.MUX_DM_MOD_2}[data["RR"]]
                    )
                    self.tick(2)
                self.data_path.signal_wr(magic_numbers.MUX_L_AC, magic_numbers.MUX_R_1, {"op": "MUL"})
                if data["RR"] != 2:
                    self.data_path.signal_adress_mod(magic_numbers.MUX_DM_MOD_1)
            if data["F"] == 1:  # MOV [[5]] A
                self.tick(4)
                self.data_path.signal_latch_ar(
                    magic_numbers.MUX_L_0, magic_numbers.MUX_R_DR, {"op": "ADD", "crop_right_to_int16": True}
                )
                self.data_path.signal_oe()
                self.data_path.signal_latch_ar(magic_numbers.MUX_L_0, magic_numbers.MUX_R_DR, {"op": "ADD"})
                self.data_path.signal_wr(magic_numbers.MUX_L_AC, magic_numbers.MUX_R_1, {"op": "MUL"})
            if data["F"] == 2:  # MOV [A+5] A
                self.tick(3)
                self.data_path.signal_latch_ar(
                    magic_numbers.MUX_L_AC, magic_numbers.MUX_R_DR, {"op": "ADD", "crop_right_to_int16": True}
                )
                self.data_path.signal_oe()
                self.data_path.signal_wr(magic_numbers.MUX_L_AC, magic_numbers.MUX_R_1, {"op": "MUL"})
            if data["F"] == 3:  # MOV [[A+5]] A
                self.tick(4)
                self.data_path.signal_latch_ar(
                    magic_numbers.MUX_L_AC, magic_numbers.MUX_R_DR, {"op": "ADD", "crop_right_to_int16": True}
                )
                self.data_path.signal_oe()
                self.data_path.signal_latch_ar(magic_numbers.MUX_L_0, magic_numbers.MUX_R_DR, {"op": "ADD"})
                self.data_path.signal_wr(magic_numbers.MUX_L_AC, magic_numbers.MUX_R_1, {"op": "MUL"})
            if data["F"] == 4:  # MOV [IP+5] A
                raise "E625"
            if data["F"] == 5:  # MOV [[IP+5]] A
                raise "E627"
            if data["F"] == 6:  # MOV [SP+5] A
                self.tick(3)
                self.data_path.signal_latch_ar(
                    magic_numbers.MUX_L_0, magic_numbers.MUX_R_DR, {"op": "ADD", "crop_right_to_int16": True}
                )
                self.data_path.signal_latch_ar(magic_numbers.MUX_L_AR, magic_numbers.MUX_R_SP, {"op": "ADD"})
                self.data_path.signal_wr(magic_numbers.MUX_L_AC, magic_numbers.MUX_R_1, {"op": "MUL"})
            if data["F"] == 7:  # MOV [[SP+5]] A
                self.tick(5)
                self.data_path.signal_latch_ar(
                    magic_numbers.MUX_L_0, magic_numbers.MUX_R_DR, {"op": "ADD", "crop_right_to_int16": True}
                )
                self.data_path.signal_latch_ar(magic_numbers.MUX_L_AR, magic_numbers.MUX_R_SP, {"op": "ADD"})
                self.data_path.signal_oe()
                self.data_path.signal_latch_ar(magic_numbers.MUX_L_0, magic_numbers.MUX_R_DR, {"op": "ADD"})
                if data["RR"] != 2:
                    self.data_path.signal_adress_mod(
                        {0: magic_numbers.MUX_DM_MOD_4, 1: magic_numbers.MUX_DM_MOD_2}[data["RR"]]
                    )
                    self.tick(2)
                self.data_path.signal_wr(magic_numbers.MUX_L_AC, magic_numbers.MUX_R_1, {"op": "MUL"})
                if data["RR"] != 2:
                    self.data_path.signal_adress_mod(magic_numbers.MUX_DM_MOD_1)
        elif instr == 4:  # ADD [5]
            if data["F"] == 0:  # ADD 5
                self.tick()
                self.data_path.signal_latch_ac(
                    magic_numbers.MUX_L_AC,
                    magic_numbers.MUX_R_DR,
                    {
                        "op": ["ADC", "ADD", "SBC", "SUB", "OR", "XOR", "AND", "MUL", "SHR", "SHL", "CMP", "MOD"][
                            data["OPER"]
                        ],
                        "crop_right_to_int16": True,
                        "set_flag": True,
                    },
                )
            elif data["F"] == 1:  # ADD [5]
                self.tick(3)
                self.data_path.signal_latch_ar(
                    magic_numbers.MUX_L_0, magic_numbers.MUX_R_DR, {"op": "ADD", "crop_right_to_int16": True}
                )
                self.data_path.signal_oe()
                self.data_path.signal_latch_ac(
                    magic_numbers.MUX_L_AC,
                    magic_numbers.MUX_R_DR,
                    {
                        "op": ["ADC", "ADD", "SBC", "SUB", "OR", "XOR", "AND", "MUL", "SHR", "SHL", "CMP", "MOD"][
                            data["OPER"]
                        ],
                        "set_flag": True,
                    },
                )
            elif data["F"] == 2:  # ADD A+5
                raise "E594"
            elif data["F"] == 3:  # ADD [A+5]
                self.tick(3)
                self.data_path.signal_latch_ar(
                    magic_numbers.MUX_L_AC, magic_numbers.MUX_R_DR, {"op": "ADD", "crop_right_to_int16": True}
                )
                self.data_path.signal_oe()
                self.data_path.signal_latch_ac(
                    magic_numbers.MUX_L_AC,
                    magic_numbers.MUX_R_DR,
                    {
                        "op": ["ADC", "ADD", "SBC", "SUB", "OR", "XOR", "AND", "MUL", "SHR", "SHL", "CMP", "MOD"][
                            data["OPER"]
                        ],
                        "set_flag": True,
                    },
                )
            elif data["F"] == 4:  # ADD IP+5
                raise "E594"
            elif data["F"] == 5:  # ADD [IP+5]
                raise "E596"
            elif data["F"] == 6:  # ADD SP+5
                raise "E602"
            elif data["F"] == 7:  # ADD [SP+5]
                if data["RR"] != 2:
                    raise "E601"
                self.tick(4)
                self.data_path.signal_latch_ar(magic_numbers.MUX_L_0, magic_numbers.MUX_R_SP, {"op": "ADD"})
                self.data_path.signal_latch_ar(
                    magic_numbers.MUX_L_AR, magic_numbers.MUX_R_DR, {"op": "ADD", "crop_right_to_int16": True}
                )
                self.data_path.signal_oe()
                self.data_path.signal_latch_ac(
                    magic_numbers.MUX_L_AC,
                    magic_numbers.MUX_R_DR,
                    {
                        "op": ["ADC", "ADD", "SBC", "SUB", "OR", "XOR", "AND", "MUL", "SHR", "SHL", "CMP", "MOD"][
                            data["OPER"]
                        ],
                        "set_flag": True,
                    },
                )
        elif instr == 5:  # ['NOT','NEG','RCL','RCR','ZEXT8','ZEXT16','EXT8','EXT16']
            self.tick(1)
            self.data_path.signal_latch_ac(
                magic_numbers.MUX_L_AC,
                magic_numbers.MUX_R_DR,
                {
                    "un": ["NOT", "NEG", "RCL", "RCR", "ZEXT8", "ZEXT16", "EXT8", "EXT16"][data["OPER"]],
                    "set_flag": True,
                },
            )
        elif instr == 6:  # INT
            if data["INT_CODE"] == 0:  # OUT
                self.tick(1)
                self.data_path.signal_out()
            elif data["INT_CODE"] == 1:  # IN
                self.tick(1)
                self.data_path.signal_latch_ac(None, None, {}, magic_numbers.MUX_A_INP)
            elif data["INT_CODE"] == 2:  # MALLOC32
                self.tick(2)
                self.data_path.signal_malloc(magic_numbers.MUX_L_AC, magic_numbers.MUX_R_1, {"op": "MUL"})
                self.data_path.signal_latch_ac(magic_numbers.MUX_L_0, magic_numbers.MUX_R_DR, {"op": "ADD"})
            elif data["INT_CODE"] == 3:  # MALLOC16
                self.tick(3)
                self.data_path.signal_malloc(
                    magic_numbers.MUX_L_AC, magic_numbers.MUX_R_1, {"op": "MUL", "ceil_div_2": True}
                )
                self.data_path.signal_latch_ac(magic_numbers.MUX_L_0, magic_numbers.MUX_R_DR, {"op": "ADD"})
                self.data_path.signal_latch_ac(
                    magic_numbers.MUX_L_AC, magic_numbers.MUX_R_1, {"op": "MUL", "unceil_div_2": True}
                )
            elif data["INT_CODE"] == 4:  # MALLOC8
                self.tick(3)
                self.data_path.signal_malloc(
                    magic_numbers.MUX_L_AC, magic_numbers.MUX_R_1, {"op": "MUL", "ceil_div_4": True}
                )
                self.data_path.signal_latch_ac(magic_numbers.MUX_L_0, magic_numbers.MUX_R_DR, {"op": "ADD"})
                self.data_path.signal_latch_ac(
                    magic_numbers.MUX_L_AC, magic_numbers.MUX_R_1, {"op": "MUL", "unceil_div_4": True}
                )
        elif instr == 7:  # reserved
            raise "E678"
        elif instr in (8, 10):  # CALL(8) and JMP(10)
            need_jump = False
            if data["COND"] == 0:
                need_jump = True
            elif data["COND"] == 1 and self.data_path.zero():
                need_jump = True
            elif data["COND"] == 2 and not self.data_path.zero():
                need_jump = True
            elif (
                data["COND"] == 3
                and ((self.data_path.sign() ^ self.data_path.overflow()) or self.data_path.zero()) == 0
            ):
                need_jump = True
            elif data["COND"] == 4 and (self.data_path.sign() ^ self.data_path.overflow()) == 1:
                need_jump = True
            elif data["COND"] == 5 and (self.data_path.sign() ^ self.data_path.overflow()) == 0:
                need_jump = True
            elif (
                data["COND"] == 6
                and ((self.data_path.sign() ^ self.data_path.overflow()) or self.data_path.zero()) == 1
            ):
                need_jump = True
            # print(data["COND"],self.data_path.zero(), need_jump)
            if instr == 8 and need_jump:
                if data["F"] == 0:  # CALL 5
                    self.tick(4)
                    self.data_path.signal_latch_sp(magic_numbers.MUX_S_INC)
                    self.data_path.signal_latch_ar(magic_numbers.MUX_L_0, magic_numbers.MUX_R_SP, {"op": "ADD"})
                    self.data_path.signal_wr(magic_numbers.MUX_L_0, magic_numbers.MUX_R_IP, {"op": "ADD"})
                    self.data_path.signal_latch_ip(
                        magic_numbers.MUX_L_0, magic_numbers.MUX_R_DR, {"op": "ADD", "crop_right_to_int16": True}
                    )
                elif data["F"] == 4:  # CALL IP+5
                    self.tick(5)
                    self.data_path.signal_latch_sp(magic_numbers.MUX_S_INC)
                    self.data_path.signal_latch_ar(magic_numbers.MUX_L_0, magic_numbers.MUX_R_SP, {"op": "ADD"})
                    self.data_path.signal_wr(magic_numbers.MUX_L_0, magic_numbers.MUX_R_IP, {"op": "ADD"})
                    self.data_path.signal_latch_ar(magic_numbers.MUX_L_0, magic_numbers.MUX_R_IP, {"op": "ADD"})
                    self.data_path.signal_latch_ip(
                        magic_numbers.MUX_L_AR, magic_numbers.MUX_R_DR, {"op": "ADD", "crop_right_to_int16": True}
                    )
                else:
                    raise "E709"
            if instr == 10 and need_jump:
                # print('!!!')
                if data["F"] == 0:  # JMP 5
                    self.tick()
                    self.data_path.signal_latch_ip(
                        magic_numbers.MUX_L_0, magic_numbers.MUX_R_DR, {"op": "ADD", "crop_right_to_int16": True}
                    )
                elif data["F"] == 4:  # JMP IP+5
                    self.tick(2)
                    self.data_path.signal_latch_ar(magic_numbers.MUX_L_0, magic_numbers.MUX_R_IP, {"op": "ADD"})
                    self.data_path.signal_latch_ip(
                        magic_numbers.MUX_L_AR, magic_numbers.MUX_R_DR, {"op": "ADD", "crop_right_to_int16": True}
                    )
                else:
                    raise "E717"
        elif instr == 9:  # RET
            # print(self.data_path.memory_manager.getmem(1))
            self.tick(4)
            self.data_path.signal_latch_ar(magic_numbers.MUX_L_0, magic_numbers.MUX_R_SP, {"op": "ADD"})
            self.data_path.signal_oe()
            self.data_path.signal_latch_ip(magic_numbers.MUX_L_0, magic_numbers.MUX_R_DR, {"op": "ADD"})
            self.data_path.signal_latch_sp(magic_numbers.MUX_S_DEC)
            # print(self.data_path.rDR)
        elif instr == 11:  # PUSH
            self.tick()
            self.data_path.signal_latch_sp(magic_numbers.MUX_S_INC)
            if data["F"] == 0:  # PUSH 5
                self.tick(2)
                self.data_path.signal_latch_ar(magic_numbers.MUX_L_0, magic_numbers.MUX_R_SP, {"op": "ADD"})
                self.data_path.signal_wr(
                    magic_numbers.MUX_L_0, magic_numbers.MUX_R_DR, {"op": "ADD", "crop_right_to_int16": True}
                )
            elif data["F"] == 1:  # PUSH [5]
                self.tick(4)
                self.data_path.signal_latch_ar(
                    magic_numbers.MUX_L_0, magic_numbers.MUX_R_DR, {"op": "ADD", "crop_right_to_int16": True}
                )
                self.data_path.signal_oe()
                self.data_path.signal_latch_ar(magic_numbers.MUX_L_0, magic_numbers.MUX_R_SP, {"op": "ADD"})
                self.data_path.signal_wr(magic_numbers.MUX_L_0, magic_numbers.MUX_R_DR, {"op": "ADD"})
            elif data["F"] == 2:  # PUSH A+5
                self.tick(2)
                self.data_path.signal_latch_ar(magic_numbers.MUX_L_0, magic_numbers.MUX_R_SP, {"op": "ADD"})
                self.data_path.signal_wr(
                    magic_numbers.MUX_L_AC, magic_numbers.MUX_R_DR, {"op": "ADD", "crop_right_to_int16": True}
                )
            elif data["F"] == 3:  # PUSH [A+5]
                self.tick(4)
                self.data_path.signal_latch_ar(
                    magic_numbers.MUX_L_AC, magic_numbers.MUX_R_DR, {"op": "ADD", "crop_right_to_int16": True}
                )
                self.data_path.signal_oe()
                self.data_path.signal_latch_ar(magic_numbers.MUX_L_0, magic_numbers.MUX_R_SP, {"op": "ADD"})
                self.data_path.signal_wr(magic_numbers.MUX_L_0, magic_numbers.MUX_R_DR, {"op": "ADD"})
            elif data["F"] == 4:  # PUSH IP+5
                raise "E722"
            elif data["F"] == 5:  # PUSH [IP+5]
                raise "E723"
            elif data["F"] == 6:  # PUSH SP+5
                raise "E726"
            elif data["F"] == 7:  # PUSH [SP+5]
                raise "E737"
        elif instr == 12:  # POP
            self.tick(4)
            self.data_path.signal_latch_ar(magic_numbers.MUX_L_0, magic_numbers.MUX_R_SP, {"op": "ADD"})
            self.data_path.signal_oe()
            self.data_path.signal_latch_ac(magic_numbers.MUX_L_0, magic_numbers.MUX_R_DR, {"op": "ADD"})
            self.data_path.signal_latch_sp(magic_numbers.MUX_S_DEC)
        elif instr == 13:  # SWAP
            if data["F"] == 6:  # SWAP SP+5
                self.tick(5)
                self.data_path.signal_latch_ar(magic_numbers.MUX_L_0, magic_numbers.MUX_R_SP, {"op": "ADD"})
                self.data_path.signal_latch_ar(
                    magic_numbers.MUX_L_AR, magic_numbers.MUX_R_DR, {"op": "ADD", "crop_right_to_int16": True}
                )
                self.data_path.signal_oe()
                (self.data_path.rDR, self.data_path.rAC) = (self.data_path.rAC, self.data_path.rDR)
                self.data_path.signal_wr(magic_numbers.MUX_L_0, magic_numbers.MUX_R_DR, {"op": "ADD"})

            else:
                raise "E741"

    def decode_and_execute_instruction(self):
        # INSTRRxx.INT_CODE.AAAAAAAA.AAAAAAAA
        # INSTRRxx.OPERxFFF.AAAAAAAA.AAAAAAAA
        # INSTRRxx.CONDxFFF.AAAAAAAA.AAAAAAAA
        # - `signal_latch_ip` -- защёлкивание адреса следующей выполняемой команды
        # - `signal_latch_ac` -- защёлкивание аккумулятора
        # - `signal_latch_ar` -- защёлкивание адреса в памяти
        # - `signal_latch_sp` -- защёлкивание адреса вершины стека
        # - `signal_oe` -- чтение из память
        # - `signal_wr` -- запись в память
        # - `signal_malloc` -- выделение памяти
        # - `signal_out` -- вывод в порт.

        self.data_path.signal_latch_ar(magic_numbers.MUX_L_0, magic_numbers.MUX_R_IP, {"op": "ADD"})
        self.data_path.signal_oe()
        self.data_path.signal_latch_ip(magic_numbers.MUX_L_AR, magic_numbers.MUX_R_1, {"op": "ADD"})
        instr = self.data_path.alu(magic_numbers.MUX_L_0, magic_numbers.MUX_R_DR, {"op": "ADD"})
        # print(instr)
        inst = instr >> (8 + 8 + 8 + 4) & 0xF
        rr = instr >> (8 + 8 + 8 + 2) & 0x3
        int_code = instr >> (8 + 8) & 0xFF
        oper = instr >> (8 + 8 + 4) & 0xF
        cond = instr >> (8 + 8 + 4) & 0xF
        F = instr >> (8 + 8) & 0x7
        A = instr & 0xFFFF
        self.execute_instruction(inst, {"RR": rr, "INT_CODE": int_code, "OPER": oper, "COND": cond, "F": F, "A": A})
        # WRITE PROGRAMM FOR RETURN OBJECT:
        # {
        #   INST: 0-15
        #   RR: 0-4
        #   INT_CODE: 0-255
        #   OPER: 0-15
        #   COND: 0-15
        #   FFF: 0-7
        #   A: INT16
        # }

    def __repr__(self):  # TODO OF C S Z
        return "TICK: {:4} ACC: {:6} SP: {:6} AR: {:6} IP: {:6} Flags: {} OUT: {} INST: {}".format(
            self._tick,
            self.data_path.rAC,
            self.data_path.rSP,
            self.data_path.rAR,
            self.data_path.rIP,
            self.data_path.alu_flags,
            self.data_path.output_buffer,
            programm[self.data_path.rIP],
        )


def simulation(mm, input_tokens, limit):
    data_path = DataPath(mm, input_tokens)
    control_unit = ControlUnit(data_path)
    instr_counter = 0

    logging.debug("%s", control_unit)
    try:
        while instr_counter < limit:
            control_unit.decode_and_execute_instruction()
            instr_counter += 1
            logging.debug("%s", control_unit)
    except EOFError:
        logging.warning("Input buffer is empty!")
    except TypeError:
        pass

    if instr_counter >= limit:
        logging.warning("Limit exceeded!")
    logging.info("output_buffer: %s", repr("".join(data_path.output_buffer)))
    return "".join(data_path.output_buffer), instr_counter, control_unit.current_tick()


def main(code_file, input_file, debug_file=None):
    mm = MemoryManager()

    def read_code(file_name):
        try:
            load_program(mm, file_name)
            if error_list:
                for i in error_list:
                    print(i)
                exit(1)
        except:
            print("Reading code error")
            exit(1)

    if debug_file is not None:
        logging.basicConfig(filename=debug_file, filemode="w", level=logging.DEBUG, force=True)
    read_code(code_file)
    input_token = []
    with open(input_file, encoding="utf-8") as file:
        input_text = file.read()
        for char in input_text:
            input_token.append(ord(char))
        input_token.append(0)

    output, instr_counter, ticks = simulation(mm, input_tokens=input_token, limit=1500)

    print("".join(output))
    print("instr_counter: ", instr_counter, "ticks:", ticks)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    assert len(sys.argv) == 3, "Wrong arguments: machine.py <code_file> <input_file>"
    _, code_file, input_file = sys.argv
    main(code_file, input_file)
