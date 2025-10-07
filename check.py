#进行提交前的基本格式检查、编译检查、数据测试
#Heai@2450313
import os
import chardet
import subprocess
import time
import argparse
import colorama

HEADER = "/* 学号 姓名 班级 */"
TARGET_ENCODING = "GB2312"

def fprint(print_data: str, color: int):
    if color == 0:
        print(f"\033[1;32m{print_data}\033[0m")
    elif color == 1:
        print(f"\033[1;31m{print_data}\033[0m")

def run_program(command, input_data = None) -> list:
    try:
        result = subprocess.run(command, shell=True, input=input_data, capture_output=True, text=True, timeout=60)
        return [result.stdout, result.stderr]
    except Exception as e:
        print(f"运行程序 {command} 时出现异常：{e}")
        return []

def clean(_tmp_path: str):
    run_program(f"rmdir /s /q {_tmp_path[:-1]}")

def correct_file(file_path: str):
    print(f"检查源文件：{file_path}")

    # 检测并转换编码
    e = 0
    with open(file_path, "rb") as f:
        rawdata = f.read()
    result = chardet.detect(rawdata)
    current_encoding = result["encoding"]
    if (current_encoding != None) and (current_encoding.upper() != TARGET_ENCODING):
        if result["confidence"] > 0.98:
            content = rawdata.decode(current_encoding, errors="replace")
            print(f"Warning：文件编码为{current_encoding}，不是{TARGET_ENCODING}，将转换为{TARGET_ENCODING}")
            encoding_modified = True
        else:
            content = rawdata.decode(current_encoding, errors="replace")
            print(f"Error：文件编码检测为{current_encoding}，但置信度低({result['confidence']})")
            e = 1
            encoding_modified = False
    else:
        content = rawdata.decode("GB2312", errors="replace")
        # print(f"文件编码为{current_encoding}")
        encoding_modified = False

    # 检查并添加首行
    lines = content.splitlines(keepends=True)
    if lines[0].strip() != HEADER:
        if lines[0].strip()[:2] == "//" or lines[0].strip()[:2] == "/*":
            print(f"Warning：首行注释内容不是{HEADER}，将修改")
            lines[0] = HEADER + "\r\n"
        else:
            print(f"Warning：首行注释不存在，将添加{HEADER}")
            lines.insert(0, HEADER + "\r\n")
        firstline_modified = True
    else:
        # print("正确的首行已存在")
        firstline_modified = False

    # 检测并替换制表符&行尾格式
    line1_modified = False
    line2_modified = False
    new_lines = []
    for line in lines[:-1]:
        if "    " in line:
            line1_modified = True
        if not line.endswith("\r\n"):
            line = line.rstrip("\r\n") + "\r\n"
            line2_modified = True
        new_lines.append(line)
    new_lines.append(lines[-1])
    # if line1_modified:
    #     print("Warning：发现四空格")
    # else:
        # print("缩进未使用四空格")
    if line2_modified:
        print("Warning：行尾非CRLF，将其替换为CRLF")
    # else:
    #     print("行尾为正确的CRLF")

    if e:
        fprint("出现Error，请手动检查，文件未修改", 1)
    elif encoding_modified or firstline_modified or line2_modified:
        backup_path = file_path + ".back"
        os.rename(file_path, backup_path)
        print(f"原文件已备份为:{backup_path}")
        with open(file_path, "w", encoding=TARGET_ENCODING, newline="") as f:
            f.writelines(new_lines)
        fprint("文件已修正", 1)
    else:
        fprint("文件格式正确", 0)
    print("-" * 80)

def msvc_compile(_source_path: str, _exe_path: str, _tmp_path: str):
    print(f"MSVC：{_source_path} → {_exe_path}")
    compile_cmd = r'set PATH=D:\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.44.35207\bin\Hostx64\x86;%PATH% && set INCLUDE=D:\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.44.35207\include;D:\Windows Kits\10\Include\10.0.22621.0\cppwinrt;D:\Windows Kits\10\Include\10.0.22621.0\shared;D:\Windows Kits\10\Include\10.0.22621.0\ucrt;D:\Windows Kits\10\Include\10.0.22621.0\um;D:\Windows Kits\10\Include\10.0.22621.0\winrt; && set LIB=D:\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.44.35207\lib\x86;D:\Windows Kits\10\Lib\10.0.22621.0\ucrt\x86;D:\Windows Kits\10\Lib\10.0.22621.0\ucrt_enclave\x86;D:\Windows Kits\10\Lib\10.0.22621.0\um\x86; && cl "' + _source_path + '" /JMC /ZI /MDd /nologo /W3 /sdl /EHsc /RTC1 /GS /Zc:wchar_t /Zc:inline /fp:precise /permissive- /WX- /Zc:forScope /Gd /Gm- /Od /Oy- /D "WIN32" /D "_DEBUG" /D "_CONSOLE" /D "_UNICODE" /D "UNICODE" /Fo"' + _tmp_path + 'tmp1.obj" /Fd"'+ _tmp_path + 'tmp1.pdb" /Fe"' + _exe_path + '" /analyze- /FC'
    out = run_program(compile_cmd, None)
    if any("error" in i.lower() for i in out[0].splitlines()):
        for i in out[0].splitlines():
            print(i)
        clean(_tmp_path)
        raise Exception("MSVC Error")
    elif len(out[0].splitlines()) == 1:
        fprint("MSVC编译通过", 0)
    else:
        fprint(out[0], 1)
    print("-" * 80)

def gcc_compile(_source_path: str, _exe_path: str, _tmp_path: str, _tp: str):
    print(f"GCC：{_source_path} → {_exe_path}")
    if _tp == "c":
        compile_cmd = r'set PATH=C:\Program Files (x86)\Dev-Cpp\MinGW64\libexec\gcc\x86_64-w64-mingw32\9.2.0;C:\Program Files (x86)\Dev-Cpp\MinGW64\bin;%PATH% && gcc "' + _source_path + '" -o "' + _exe_path + r'" -m32 -g3 -I"C:\Program Files (x86)\Dev-Cpp\MinGW64\include" -I"C:\Program Files (x86)\Dev-Cpp\MinGW64\x86_64-w64-mingw32\include" -I"C:\Program Files (x86)\Dev-Cpp\MinGW64\lib\gcc\x86_64-w64-mingw32\9.2.0\include" -L"C:\Program Files (x86)\Dev-Cpp\MinGW64\x86_64-w64-mingw32\lib32" -static-libgcc -m32 -g3'
    elif _tp == "cpp":
        compile_cmd = r'set PATH=C:\Program Files (x86)\Dev-Cpp\MinGW64\libexec\gcc\x86_64-w64-mingw32\9.2.0;C:\Program Files (x86)\Dev-Cpp\MinGW64\bin;%PATH% && g++ "' + _source_path + '" -o "' + _exe_path + r'" -m32 -g3 -I"C:\Program Files (x86)\Dev-Cpp\MinGW64\include" -I"C:\Program Files (x86)\Dev-Cpp\MinGW64\x86_64-w64-mingw32\include" -I"C:\Program Files (x86)\Dev-Cpp\MinGW64\lib\gcc\x86_64-w64-mingw32\9.2.0\include" -I"C:\Program Files (x86)\Dev-Cpp\MinGW64\lib\gcc\x86_64-w64-mingw32\9.2.0\include\c++" -L"C:\Program Files (x86)\Dev-Cpp\MinGW64\x86_64-w64-mingw32\lib32" -static-libgcc -m32 -g3'
    out = run_program(compile_cmd, None)
    if out[1] != "":
        if any("error" in i.lower() for i in out[1].splitlines()):
            print(out[1])
            clean(_tmp_path)
            raise Exception("GCC Error")
        else:
            fprint(out[1], 1)
    else:
        fprint("GCC编译通过", 0)
    print("-" * 80)

def convert_path_to_wsl(_path: str) -> str:
    drive, tail = os.path.splitdrive(_path)
    drive_letter = drive[0].lower()
    wsl_path = f"/mnt/{drive_letter}{tail.replace(os.sep, '/')}"
    return wsl_path

def linux_compile(_source_path: str, _exe_path: str, _tp: str):
    _source_path = convert_path_to_wsl(_source_path)
    _exe_path = convert_path_to_wsl(_exe_path)
    print(f"Linux GCC：{_source_path} → {_exe_path}")
    if _tp == "c":
        compile_cmd = ["wsl", "gcc", "-Wall", "-o", _exe_path, _source_path, "-lm"]
    elif _tp == "cpp":
        compile_cmd = ["wsl", "c++", "-Wall", "-o", _exe_path, _source_path, "-lm"]
    result = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=60, encoding="utf-8")
    if any("error" in i.lower() for i in result.stderr.splitlines()):
        for i in result.stderr.splitlines():
            print(i)
        raise Exception("Linux gcc Error")
    elif len(result.stderr.splitlines()) == 0:
        fprint("Linux GCC编译通过", 0)
    else:
        fprint(result.stderr, 1)
    print("-" * 80)

def get_test_data_list(_data_path: str, _num: int) -> list:
    print("getting test data")
    with open(_data_path, "r") as f:
        a = f.readlines()
    if a[0] == "_NODATA_":
        test_data = [None]
    else:
        if _num == 0:
            test_data = a
        else:
            test_data = a[:_num]
        if test_data[-1][-1] != "\n":
            test_data[-1] += "\n"
        for i in range(len(test_data)):
            if "\\n" in test_data[i]:
                test_data[i] = test_data[i].replace("\\n", "\n")
            else:
                test_data[i] = test_data[i].replace(" ", "\n")
    print(len(test_data))
    print("-" * 80)
    return test_data

def pydata_test(test_program: str, demo_program: str, _test_data_list: list, _ignore_lines: int, _detailed_flag: int, is_linux: bool = False):
    e = 0
    if is_linux:
        test_program = convert_path_to_wsl(test_program)
    print("pychecking " + test_program + " && " + demo_program)
    for idx, test_input in enumerate(_test_data_list, start=1):
        if idx % 100 == 0:
            print(idx, end="...")
        if is_linux:
            output1 = subprocess.run(["wsl", test_program], input=test_input, capture_output=True, text=True, timeout=60).stdout.splitlines(keepends=True)
        else:
            output1 = run_program([test_program], test_input)[0].splitlines(keepends=True)
        output2 = run_program([demo_program], test_input)[0].splitlines(keepends=True)
        output1 = "".join(output1[:-_ignore_lines]) if _ignore_lines < len(output1) and _ignore_lines != 0 else "".join(output1)
        output2 = "".join(output2[:-_ignore_lines]) if _ignore_lines < len(output2) and _ignore_lines != 0 else "".join(output2)
        if(_detailed_flag == 1):
            print(output1[:-1])
        if idx == 1 and len(output1) < 5 or len(output2) < 5:
            Exception("输出结果过短，可能编译错误/路径错误")
        if output1 != output2:
            e += 1
            dat = f"输入数据:{test_input}{test_program}输出:\n{output1}\n{demo_program}输出:\n{output2}\n" + "-" * 80
            print(f"测试{idx}：FAIL\n" + dat)
    if e == 0:
        fprint(str(len(_test_data_list)) + " data all passed.", 0)
    else:
        fprint("错误数据数/总数据数：" + str(e) + "/" + str(len(_test_data_list)), 1)
    print("-" * 80)

def tcdata_test(test_program: str, demo_program: str, test_data: list, _ignore_lines: int, is_linux: bool = False):
    if _ignore_lines == 0:
        if is_linux:
            test_program = convert_path_to_wsl(test_program)
        print("tcchecking " + test_program + " && " + demo_program)
        run_program(["del", "tmpresult1.txt"])
        run_program(["del", "tmpresult2.txt"])
        for i in test_data:
            if is_linux:
                subprocess.run(["wsl", test_program, ">>", "tmpresult1.txt"], input=i, capture_output=True, text=True, timeout=60)
            else:
                run_program([test_program, ">>", "tmpresult1.txt"], i)
            run_program([demo_program, ">>", "tmpresult2.txt"], i)
        if is_linux:
            print(run_program(["txt_compare", "--file1", "tmpresult1.txt", "--file2", "tmpresult2.txt", "--display", "normal"])[0][:-1])
        else:
            print(run_program(["txt_compare", "--file1", "tmpresult1.txt", "--file2", "tmpresult2.txt", "--CR_CRLF_not_equal", "--display", "normal"])[0][:-1])
        print("-" * 80)
        run_program(["del", "tmpresult1.txt"])
        run_program(["del", "tmpresult2.txt"])

if __name__ == '__main__':
    colorama.init()
    argp = argparse.ArgumentParser(description="Compile and check C/C++ source code")
    argp.add_argument("name", help="Name of the source file (without extension)")
    argp.add_argument("tp", choices=["c", "cpp"], help="Type of the source file (c or cpp)")
    argp.add_argument("-n", "--num", type=int, default=0, help="Number of test data lines to read from the file(default: 0 for all)")
    argp.add_argument("-d", "--demo", choices=["c", "cpp", "msvc", "gcc"], help="Specify demo program name (without x-x-demo-)")
    argp.add_argument("-nc", "--nocompile", action="store_true", help="Test the exe without sourcefile")
    argp.add_argument("-il", "--ignorelines", type=int, default=0, help="Ignore the last N lines of the output(unsupport txt_compare)")
    argp.add_argument("-dt", "--detailed", action="store_true", help="Print detailed output")
    args = argp.parse_args()
    name = args.name # name为不含文件类型后缀的代码文件名
    # name1为去掉-1/-2后缀的文件名，part为项目类型（实验课/作业）（即解决方案名）
    # name1在高程一些作业的情况下用到了，oop情境忽略即可
    if name[0] == "w":
        name1 = name
        part = "experimentwork"
    elif name[-2] == "-":
        name1 = name[:-2]
        part = f"homework-{name[0]}{name[1]}"
    else:
        name1 = name
        part = f"homework-{name[0]}{name[1]}"
    num = args.num # num为读取的测试数据组数，默认值0为读取全部
    tp = args.tp # tp为代码文件类型（c/cpp）
    ignore_lines = args.ignorelines # ignore_lines为忽略的输出最后几行的行数，默认值0为不忽略
    detailed_flag = args.detailed # flag为是否打印详细输出，默认值0为不打印

    root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # oop作业总文件夹路径
    if not(args.nocompile):
        tmp_path = f"{root_path}\\tmp{name}\\"
    else: # -nc时仅对exe进行数据测试，需测试的exe放入tmp文件夹，文件名改为tmp1.exe
        tmp_path = f"{root_path}\\tmp\\"
    if tp == "c":
        source_path = f"{root_path}\\programwork\\{part}\\{name}c\\{name}.c"
    elif tp == "cpp":
        source_path = f"{root_path}\\programwork\\{part}\\{name}\\{name}.cpp"
    if args.demo: # -d指定demo的后缀名
        exe_path = {"msvc" : tmp_path + "tmp1.exe", "gcc" : tmp_path + "tmp2.exe", "linux" : tmp_path + "tmp3", "demo" : root_path + "\\tools\\demo\\" + name + "-demo-" + args.demo + ".exe"}
    else:
        exe_path = {"msvc" : tmp_path + "tmp1.exe", "gcc" : tmp_path + "tmp2.exe", "linux" : tmp_path + "tmp3", "demo" : root_path + "\\tools\\demo\\" + name + "-demo.exe"}
    data_path = f"{root_path}\\tools\\test_data\\{name}.txt"

    print(time.strftime("%Y-%m-%d %H:%M", time.localtime()))
    print("-" * 80)
    clean(tmp_path[:-1])
    run_program(["mkdir", tmp_path[:-1]])

    if not(args.nocompile):
        correct_file(source_path)
        msvc_compile(source_path, exe_path["msvc"], tmp_path)
        gcc_compile(source_path, exe_path["gcc"], tmp_path, tp)
        linux_compile(source_path, exe_path["linux"], tp)

    test_data_list = get_test_data_list(data_path, num)
    if args.nocompile:
        pydata_test(exe_path["msvc"], exe_path["demo"], test_data_list, ignore_lines, detailed_flag)
        tcdata_test(exe_path["msvc"], exe_path["demo"], test_data_list, ignore_lines)
    elif args.demo:
        if args.demo == "msvc":
            pydata_test(exe_path["msvc"], exe_path["demo"], test_data_list, ignore_lines, detailed_flag)
            tcdata_test(exe_path["msvc"], exe_path["demo"], test_data_list, ignore_lines)
        elif args.demo == "gcc":
            pydata_test(exe_path["gcc"], exe_path["demo"], test_data_list, ignore_lines, detailed_flag)
            tcdata_test(exe_path["gcc"], exe_path["demo"], test_data_list, ignore_lines)
        else:
            pydata_test(exe_path["msvc"], exe_path["demo"], test_data_list, ignore_lines, detailed_flag)
            tcdata_test(exe_path["msvc"], exe_path["demo"], test_data_list, ignore_lines)
            pydata_test(exe_path["gcc"], exe_path["demo"], test_data_list, ignore_lines, detailed_flag)
            tcdata_test(exe_path["gcc"], exe_path["demo"], test_data_list, ignore_lines)
            pydata_test(exe_path["linux"], exe_path["demo"], test_data_list, ignore_lines, detailed_flag, True)
            tcdata_test(exe_path["linux"], exe_path["demo"], test_data_list, ignore_lines, True)
    else:
        pydata_test(exe_path["msvc"], exe_path["demo"], test_data_list, ignore_lines, detailed_flag)
        tcdata_test(exe_path["msvc"], exe_path["demo"], test_data_list, ignore_lines)
        pydata_test(exe_path["gcc"], exe_path["demo"], test_data_list, ignore_lines, detailed_flag)
        tcdata_test(exe_path["gcc"], exe_path["demo"], test_data_list, ignore_lines)
        pydata_test(exe_path["linux"], exe_path["demo"], test_data_list, ignore_lines, detailed_flag, True)
        tcdata_test(exe_path["linux"], exe_path["demo"], test_data_list, ignore_lines, True)

    if not(args.nocompile):
        clean(tmp_path)