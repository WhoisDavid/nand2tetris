// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

@pixel
M=0

(LOOP)
@KBD
D=M
@KEYPRESSED
D; JNE // if RAM[KBD] != 0 <=> a key is pressed

(NOKEYPRESSED)
@pixel 
D=M 
@FILL
D; JNE // when a no key is pressed, fills if pixel = -1
@LOOP
0; JMP

(KEYPRESSED)
@pixel
D=M
@FILL
D; JEQ  // when a key is pressed, fills if pixel = 0 (blank)
@LOOP
0; JMP

(FILL)
@SCREEN 
D=A
@addr 
M=D // addr = SCREEN
@pixel
M=!M // sets pixel to its complement

(LOOPFILL)
@pixel
D=M // D = pixel
@addr
A=M
M=D // RAM[addr] = pixel
@addr
MD=M+1 // addr++
@KBD // use KBD as end of loop since the screen map is on [SCREEN, KBD)
D=D-A  // D = addr - KBD
@LOOPFILL
D;JNE // LOOPS IF addr != KBD

@LOOP  
0; JMP  // back to start