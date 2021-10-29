import cx_Freeze

cx_Freeze.setup(
    name="NanJ Script Regex Helper",
    version="1.0",
    description="なんJのスクリプトのNG正規表現の制作を支援するプログラム。",
    options={"build_exe": {"optimize": 2}},
    executables=[
        cx_Freeze.Executable("get_script_threadkeys.py"),
        cx_Freeze.Executable("script_res_selector.py"),
    ],
)
