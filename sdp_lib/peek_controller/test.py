import pprint

with open('CO413.DAT') as f1, open('CmdSG.txt', 'w') as f2:
    cmd_sg = []
    xp1, xp2, xp3, xp4 = 1, 13, 18, 22
    cnt = 1
    flag = False
    for line in f1:
        if "YSRM_UK_STAGE" in line:
            flag = True

        if "CmdSG" in line and len(line) > 30:
            # f2.write(line.split(',', maxsplit=1)[-1].replace('"', ''))



            cmd_sg.append(line.split(',', maxsplit=1)[-1].replace('"', ''))
            # stages[str(cnt)] = []
            # cnt += 1

        prev_line = line

    print(*cmd_sg)

    stages = {
        '1': cmd_sg[:xp2 - 1],
        '2': cmd_sg[xp2 - 1:xp3 - 1],
        '3': cmd_sg[xp3 - 1:xp4 - 1],
        '4': cmd_sg[xp4 - 1:]
    }
    pprint.pprint(stages)
    cnt = 1
    for xp, cmd_vals in stages.items():
        f2.write(f'Process {xp}:\n')
        for l in cmd_vals:
            f2.write(f'Stage {cnt}: {l}')
            cnt += 1