# Ценеков Дмитрий P3210

Вариант: `alg -> asm | acc | neum | hw | instr | struct | stream | mem | cstr | prob2 | cache`

Базовый вариант (без усложнения)

## Язык программирования

Описание синтаксиса языка в форме БНФ:

```ebnf
<programm> ::= <instructions>
<instructions> ::= <пусто> | <instr> | <instr><instructions>
<instr> ::= <branching> |
            <type> <name>(<typed_args>) {<instructions>} | <type> <name>=<formula> | <type> <name>[<formula>] |
            <name>=<formula> | <name>[<formula>]=<formula> | <name>(<args>)

<args> ::= <formula_0> | <args>,<formula_0)>

<formula_n> ::= <name>(<args>) | <name> | <name>[<formula_0>] | <number> | "[^"]*" | '[^']*' | `[^`]*` | (<formula_0>)
                n==0: <formula_0> || <formula_0> | 
                n<=1: <formula_1> && <formula_1> | 
                n<=2: <formula_2> == <formula_2> | <formula_2> != <formula_2> |
                        <formula_2> < <formula_2> | <formula_2> > <formula_2> |
                n<=3: <formula_3> << <formula_3> | <formula_3> >> <formula_3> |
                n<=4: <formula_4> * <formula_4> | <formula_4> % <formula_4> |
                n<=5: <formula_5> + <formula_5> |  <formula_5> - <formula_5>

<typed_args> ::= <type> <name> | <typed_args>, <type> <name>

<branching> ::= do {<instructions>} while (<formula>) |
                 while (<formula>) {<instructions>} |
                 for (<instr>;<formula>;<instr>) {<instructions>} |
                 if (<formula>) {<instructions>}
```

Пример программы:

```js
int32 divide_by_10(int32 number) {
    int32 result = 0;
    while (number > 9) {
        number = number - 10;
        result = result + 1;
    }
    number = result;
}

void print_int(int32 j) {
    int8 buffer[10]
    int32 i=0;
    
    do {
        buffer[i] = j%10+48
        i = i + 1
        j = divide_by_10(j)
    } while (j!=0)
    
    while (i>0) {
        i = i - 1
        OUT(buffer[i])
    }
}

int32 i=1;
int32 res=0;
while(i<10){
    if((i%3==0)||(i%5==0)){
        res=res+i;
    }
    i=i+1
}
print_int(res)
```

Язык поддерживает всего 7 типов данных:

1. int8
2. int16
3. int32
3. str (alias int8[])
4. int8[]
5. int16[]
6. int32[]

Результат всех математических операций будет "обрезан" до младших 32-бит без завершения программы.

Результат операций сравнения возвращается как `-1` или `0`.

Отдельные символы строки имеют тип целого числа.  

Поддерживаются строковые литералы произвольной длины. В конце строки ставится символ-ноль `\0`, в соответствие с вариантом. 

Область видимости переменных -- глобальные, локальная в рамках функций и для блоков кода (`if`, `while`, `do-while`, ...).

Функции и процедуры имеют доступ только к глобальным переменным, своим локальным переменным и аргументам.

Поддерживается рекурсия.

Язык предоставляет следующие встроенные функции/процедуры:

* `int8 IN()` - читает один символ из потока ввода
* `void OUT(int8 i)` - печатает один символ в поток вывода


## Организация памяти

Система построена по архитектуре фон Неймана, то есть разделения команд и данных нет:.

Память работает в линейном, плоском адресном пространстве.

### Регистры

Система обладает аккумуляторной архитектурой. Поэтому большинство операций происходит над аккумулятором. Остальные регистры устанавливаются процессором.

```text
# EAX (16bit: AX, 8bit: AL) - 32-bit ACCUMULATOR. General purpose register
# SP - 32-bit STACK POINTER
# IP - 32-bit INSTRUCTION POINTER
# CPU 4 flags: OF - overflow, C - carry, Z - zero, S - sign
```

Никакие переменные не отображаются на регистры, так как по сути нам доступен всего один регистр -- аккумулятор.

### Память

Размер машинного слова -- 32 бит.

```
 ╔═════════════════╗
 ║    JMP START    ║
 ╚═════════════════╝
 ╔═════════════════╗
 ║      STACK      ║ # STACK_ADR = 1
 ╚═════════════════╝
 ╔═════════════════╗
 ║ GLOBAL VARIBLE  ║ # GLOBAL_VARIBLE_ADR = STACK_ADR + COMPILE_SETUP.STACK_SIZE
 ╚═════════════════╝
 ╔═════════════════╗
 ║     STRINGs     ║ # CONSTANTS_ADR = GLOBAL_VARIBLE_ADR + SIZE(GLOBAL VARIBLE)
 ╚═════════════════╝
 ╔═════════════════╗
 ║ START:          ║
 ║   main programm ║
 ║                 ║
 ║ FUNCTION 1:     ║
 ║   PUSH 0        ║ # local variable
 ║   ...           ║ # n-arg by addres SP-SIZE(local variable)-SIZE(args)-1+n
 ║                 ║
 ║ FUNCTION 2:     ║
 ║   ...           ║
 ║                 ║
 ║ ...             ║
 ║                 ║
 ║ FUNCTION N:     ║
 ║   ...           ║
 ╚═════════════════╝
```


## Система команд

|               \              |   №  | 5 (000) | [5] (001) | EAX+5 (010) | [EAX+5] (011) | IP+ARG (100) | [IP+5] (101) | SP+5 (110) | [SP+5] (111) |
|:----------------------------:|:----:|:-------:|:---------:|:-----------:|:-------------:|:------------:|:------------:|:----------:|:------------:|
|              NOP             | 0000 |         |           |             |               |              |              |            |              |
|             HALT             | 0001 |         |           |             |               |              |              |            |              |
|           MOV A, F           | 0010 |    +    |     +     |      +      |       +       |       -      |       -      |      -     |   only EAX   |
|          MOV [F], A          | 0011 |    +    |  only EAX |   only EAX  |    only EAX   |       -      |       -      |  only EAX  |       +      |
|       ADD F, ADC F, ...      | 0100 |    +    |     +     |      -      |       +       |       -      |       -      |      -     |       +      |
|         NOT, NEG, ...        | 0101 |         |           |             |               |              |              |            |              |
| INT (OUT, IN, MALLOC32, ...) | 0110 |         |           |             |               |              |              |            |              |
|            CALL F            | 1000 |    +    |     -     |      -      |       -       |       +      |       -      |      -     |       -      |
|              RET             | 1001 |         |           |             |               |              |              |            |              |
|             JMP F            | 1010 |    +    |     -     |      -      |       -       |       +      |       -      |      -     |       -      |
|            PUSH F            | 1011 |    +    |     +     |      +      |       +       |       -      |       -      |      -     |       -      |
|              POP             | 1100 |         |           |             |               |              |              |            |              |
|           SWAP [F]           | 1110 |    -    |     -     |      -      |       -       |       -      |       -      |      +     |       -      |

RAW:
```text

 MEM(32 bit address) = 32bit value by address
            000      001        010         011          100         101          110         111
 F(ARG) ::= ARG || MEM(ARG) || A+ARG || MEM(A+ARG) ||  IP+ARG || MEM(IP+ARG) ||  SP+ARG || MEM(SP+ARG)

 A ::= AL || AX || EAX || RESERVED_FOR_x64

 0000xxxx.xxxxxxxx.xxxxxxxx.xxxxxxxx NOP            NOP
 0001xxxx.xxxxxxxx.xxxxxxxx.xxxxxxxx HALT           HALT

 0010RRxx.xxxxxFFF.AAAAAAAA.AAAAAAAA MOV            A := F(ARG)            Z S
 MOV AL, -10
 MOV AL, [A-2]
 MOV AL, [IP+2]
 MOV AL, SP
 0011RRxx.xxxxxFFF.AAAAAAAA.AAAAAAAA MOV            MEM(F(ARG)) := A
 MOV [10], AH
 MOV [SP+10], AL
 MOV [[IP-1]], EAX

 OP ::= ADC || ADD || SBC || SUB || OR || XOR || AND || MUL || SHR || SHL || CMP
 0100RRxx.OPERxFFF.AAAAAAAA.AAAAAAAA ALU OP ARG                             OF C Z S
 ALU ADC AL [IP+2]
 ALU ADD EAX -10

 UOP ::= NOT || NEG || RCL || RCR || ZEXT8 || ZEXT16 || EXT8 || EXT16
 0101xxxx.OPERxxxx.xxxxxxxx.xxxxxxxx ALU UOP                                OF C Z S
 ALU NOT
 ALU RCR

 0110xxxx.00000001.xxxxxxxx.xxxxxxxx OUT         WRITE(AL);
 0110xxxx.00000010.xxxxxxxx.xxxxxxxx IN          AL := READ()
 0110xxxx.00000011.xxxxxxxx.xxxxxxxx MALLOC32    EAX := MALLOC(EAX)
 0110xxxx.00000100.xxxxxxxx.xxxxxxxx MALLOC16    EAX := MALLOC((1+EAX)>>1)<<1
 0110xxxx.00000101.xxxxxxxx.xxxxxxxx MALLOC8     EAX := MALLOC((3+EAX)>>2)<<2
 0110xxxx.00000110.xxxxxxxx.xxxxxxxx FREE        FREE(EAX);

 COND = {
   : 0000  # always
   E: 0001  # = (Z = 1)
   NE: 0010  # != (Z = 0)
   G: 0011  # > ((S xor OF) or Z = 0)
   L: 0100  # < (S xor OF = 1)
   GE: 0101  # >= (S xor OF = 0)
   LE: 0110  # <= ((S xor OF) or Z = 1)
 }
 1000xxxx.CONDxFFF.AAAAAAAA.AAAAAAAA CALL        MEM(++SP) = IP; IP = F(ARG)
 1001xxxx.CONDxFFF.AAAAAAAA.AAAAAAAA RET         IP = MEM(SP--)
 1010xxxx.CONDxFFF.AAAAAAAA.AAAAAAAA JUMP        IP = F(ARG)
 1011xxxx.xxxxxFFF.AAAAAAAA.AAAAAAAA PUSH        MEM(++SP) = F(ARG)
 1100xxxx.xxxxxxxx.xxxxxxxx.xxxxxxxx POP         F(ARG) = MEM(SP--)            Z S
 1101RRxx.xxxxxFFF.AAAAAAAA.AAAAAAAA SWAP        B=A; A=MEM(F(ARG)); MEM(F(ARG))=B            Z S
 SWAP EAX, SP
```

### Стек

У компилятора есть настройка отвечающая за размер создаваемого стека. Стек расширяется в положительную сторону начиная с 1 адреса

## Модель процессора

### Data Memory

```text
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

### Data Memory

```text
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

### ControlUnit

Блок управления процессора. Выполняет декодирование инструкций и
    управляет состоянием модели процессора, включая обработку данных (DataPath).

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


## Тестирование

Тестирование выполняется при помощи golden test-ов.

* Golden test-ы реализованы для следующих программ: 
    - [golden/hello.yml](golden/hello.yml) - напечатать hello world
    - [golden/cat.yml](golden/cat.yml) - печатать данные, поданные на вход симулятору через файл ввода (размер ввода потенциально бесконечен)
    - [golden/hello_user_name.yml](golden/hello_user_name.yml) - запросить у пользователя его имя, считать его, вывести на экран приветствие
    - [golden/prob3.yml](golden/prob1.yml) - задача №2
* Скрипт выполнения интеграционных тестов: [integration_test.py](integration_test.py)
