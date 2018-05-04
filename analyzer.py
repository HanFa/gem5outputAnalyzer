#!/usr/local/bin/python3
import sys
import enum


class InstType(enum.Enum):

    NONE = 0,
    CALL = 1,
    RETURN = 2,
    MOVLRCALL = 3,
    LDRPCRETURN = 4


class Inst:

    def __init__(self):
        self.type = InstType.NONE
        self.pc = -1
        self.isTaken = False
        self.machineCode = ''
        self.lineNumber = -1


def extractFromLine(parameter, line_words):
    """ Utility function that scan the pattern in line: <parameter> = <target>. """
    if parameter in line_words:
        if line_words[line_words.index(parameter) + 1] == '=':
            target_index = line_words.index(parameter) + 2
            assert target_index >= 2
            return line_words[target_index]

    return None


def printInst(insn, ras, verbose=True):
    """ Utility function to print the instructions flow. """
    type_str = ''
    
    if insn.type == InstType.CALL:
        type_str = 'CALL'
    elif insn.type == InstType.MOVLRCALL:
        type_str = 'MOVLRCALL'
    elif insn.type == InstType.RETURN:
        type_str = 'RETURN'
    elif insn.type == InstType.LDRPCRETURN:
        type_str = 'LDRPCRETURN'
    
    line = '\t' * len(ras) + hex(insn.pc) + " - " + type_str
    if verbose:
        print(line)
    else:
        if insn.type != InstType.NONE:
            print(line)
    return


def main():
    if len(sys.argv) != 2:
        print("Usage: ./analyzer.py <InputFile>")
        return

    lines = []
    with open(sys.argv[1], 'r') as fn:
        lines = fn.readlines()
    
    staticCallNum = 0
    staticRetNum = 0
    staticMovLRNum = 0
    staticLdrPCNum = 0

    dynamicCallNum = 0
    dynamicRetNum = 0
    dynamicMovLRNum = 0
    dynamicLdrPCNum = 0

    ras = []
    insns = []
    start_sim_line_number = -1

    for line in lines:
        if line.rstrip('\n') == '**** REAL SIMULATION ****':
            start_sim_line_number = lines.index(line) + 1

        if line.find("SYSCALL") != -1:
            staticMovLRNum += 1
        elif line.find("SYSRETURN") != -1:
            staticLdrPCNum += 1
        elif line.find("CALL") != -1:
            staticCallNum += 1
        elif line.find("RETURN") != -1:
            staticRetNum += 1

    print("--- Static SYSCALL : SYSRETURN : CALL : RETURN = {} : {} : {} : {} ---"
        .format(staticMovLRNum, staticLdrPCNum, staticCallNum, staticRetNum))

    if start_sim_line_number == -1:
        print('**** REAL SIMULATION **** pattern not found')
        return

    for idx in range(start_sim_line_number, len(lines)):
        line_words = lines[idx].rstrip('\n').split()
        cur_insn = Inst()
        if 'SYSCALL' in line_words:
            cur_insn.type = InstType.MOVLRCALL
        elif 'SYSRETURN' in line_words:
            cur_insn.type = InstType.LDRPCRETURN
        elif 'CALL' in line_words:
            cur_insn.type = InstType.CALL
        elif 'RETURN' in line_words:
            cur_insn.type = InstType.RETURN
        else:
            cur_insn.type = InstType.NONE

        cur_insn.lineNumber = int(idx)
        cur_insn.pc = extractFromLine(parameter='pc', line_words=line_words)
        cur_insn.machineCode = extractFromLine(parameter='machcode', line_words=line_words)

        if not cur_insn.pc or not cur_insn.machineCode:
            continue

        cur_insn.pc = int(cur_insn.pc, 16)


        if cur_insn.type != InstType.NONE:
            if idx + 1 >= len(lines):
                continue
     
            next_line_idx = idx + 1 if cur_insn.type != InstType.MOVLRCALL else idx + 2
            next_line_words = lines[next_line_idx].rstrip('\n').split()
            next_insn = Inst()
            next_insn.pc = extractFromLine(parameter='pc', line_words=next_line_words)
            if not next_insn.pc:
                continue

            next_insn.pc = int(next_insn.pc, 16)

            if cur_insn.type == InstType.MOVLRCALL:
                cur_insn.isTaken = not (next_insn.pc - cur_insn.pc == 8)
            else:
                cur_insn.isTaken = not (next_insn.pc - cur_insn.pc == 4)

        insns += [cur_insn]

    for insn in insns:
        if insn.isTaken:
            if insn.type == InstType.CALL:
                dynamicCallNum += 1
            elif insn.type == InstType.MOVLRCALL:
                dynamicMovLRNum += 1
            elif insn.type == InstType.RETURN:
                dynamicRetNum += 1
            elif insn.type == InstType.LDRPCRETURN:
                dynamicLdrPCNum += 1

    print("--- Dynamic SYSCALL : SYSRETURN : CALL : RETURN = {} : {} : {} : {} ---"
        .format(dynamicMovLRNum, dynamicLdrPCNum, dynamicCallNum, dynamicRetNum))


    verbose = True
    for insn in insns:
        if insn.type == InstType.CALL or insn.type == InstType.MOVLRCALL:
            if insn.isTaken:
                if insn.type == InstType.CALL:
                    dynamicCallNum += 1
                elif insn.type == InstType.MOVLRCALL:
                    dynamicMovLRNum += 1

                ras += [insn.pc + 4 if insn.type == InstType.CALL else insn.pc + 8]
                printInst(insn=insn, ras=ras, verbose=verbose)

        elif insn.type == InstType.RETURN or insn.type == InstType.LDRPCRETURN:
            if insn.isTaken:
                if insn.type == InstType.RETURN:
                    dynamicRetNum += 1
                elif insn.type == InstType.LDRPCRETURN:
                    dynamicLdrPCNum += 1

                printInst(insn=insn, ras=ras, verbose=verbose)
                ras_print = [hex(r) for r in ras[-2:]]
                print(ras_print)
                returnPC = ras.pop()
                if insns[insns.index(insn) + 1].pc != returnPC:
                	print("RAS wrong\n")
                	printInst(insn=insns[insns.index(insn) + 1], ras=ras, verbose=verbose)
                assert insns[insns.index(insn) + 1].pc == returnPC

        else:
            printInst(insn=insn, ras=ras, verbose=verbose)

if __name__ == "__main__":
    main()
