// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)

// Put your code here.
// easy way add R[0] R[1]-times
// optimize = bit by bit 
// aux = R[0]
// sum = 0
// => if R[1][i] then S+=aux
// aux += aux

// R[1][i] = (mask AND R[1]) > 0
// mask = 1  mask+=mask => (1, 2, 4, 8, 16...)
// Stop when mask > R[1]


// initialize sum = 0
@sum
M=0

// initialize aux = R[0]
@R0
D=M
@bitshift
M=D

// initialize mask = 1
@mask
M=1

(LOOP)
    @mask
    D=M
    @R1
    D=D-M
    @STOP
    D; JGT // if mask > RAM[1] then STOP

    @bitshift
    D=M
    M=M+D // = left shifts (starting from RAM[0])
    @aux
    M=D // aux stores current shift

    @mask
    D=M
    M=D+M // = left shifts (starting from 1)
    @R1
    D=D&M // Apply mask ie check if n-th bit is 1
    @LOOP
    D; JEQ // if n-th bit = 0 loop else ...

    @aux
    D=M 
    @sum
    M=M+D // sum += shift(R[0], n)

    @LOOP
    0; JMP

(STOP)
    @sum
    D=M
    @R2
    M=D // RAM[2] = sum

(END)
    @END
    0; JMP // Infinite Loop