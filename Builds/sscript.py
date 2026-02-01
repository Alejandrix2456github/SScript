import sys, os, subprocess, re, argparse, platform

# --- 1. SScript Core (The "Runtime" Library) ---
CORE_HEADER = """
#include <iostream>
#include <fstream>
#include <string>
#include <cstdlib>
#include <unistd.h>
#include <vector>

template<typename T>
void print(T msg) { std::cout << msg << std::endl; }

namespace Battery {
    int level() {
        std::ifstream file("/sys/class/power_supply/BAT0/capacity");
        int val = -1;
        if(file >> val) return val;
        return -1; 
    }
}

namespace System {
    void sleep(int sec) { ::sleep(sec); }
    std::string user() { return getenv("USER") ? getenv("USER") : "user"; }
    
    void notify(std::string t, std::string m) {
        std::string cmd = "notify-send \\""+t+"\\" \\""+m+"\\" 2>/dev/null || echo \\"Notification: "+t+" - "+m+"\\"";
        (void)!system(cmd.c_str());
    }
}

namespace File {
    void write(std::string path, std::string content) {
        std::ofstream f(path);
        f << content;
        f.close();
    }
    bool exists(std::string path) {
        return (access(path.c_str(), F_OK) != -1);
    }
}

namespace Net {
    // Perfect for fetching from cdn.jsdelivr.net
    void fetch(std::string url, std::string path) {
        std::string cmd = "curl -L -s " + url + " -o " + path;
        print("Fetching: " + url);
        (void)!system(cmd.c_str());
    }
}

namespace Hardware {
    void volume(int vol) {
        std::string cmd = "amixer set Master " + std::to_string(vol) + "% > /dev/null 2>&1";
        (void)!system(cmd.c_str());
    }
}
"""

# --- 2. Transpiler Logic ---
def transpile(ss_code):
    lines = ss_code.splitlines()
    cpp_lines = []
    
    # Detect if user wrote their own main entry point
    has_main = any(re.search(r'\b(fn|int)\s+main\(', line) for line in lines)
    
    for line in lines:
        raw = line.strip()
        if not raw or raw.startswith("#"): continue
        
        # Syntax Sugar
        line = re.sub(r'\bvar\b', 'auto', line)
        line = re.sub(r'\bfn\s+', 'void ', line)
        line = line.replace('void main()', 'int main()')
        
        # Module Access (Dot notation to C++ Scope)
        modules = ["Battery", "System", "File", "Net", "Hardware"]
        for mod in modules:
            line = line.replace(f"{mod}.", f"{mod}::")

        # Automatic semicolon insertion
        if not raw.endswith(("{", "}", ";", ":")):
            line += ";"
        cpp_lines.append(line)

    body = "\n    ".join(cpp_lines)
    
    # Wrap in main() if it's a loose script
    if not has_main:
        return f"{CORE_HEADER}\nint main() {{\n    {body}\n    return 0;\n}}"
    
    return f"{CORE_HEADER}\n" + "\n".join(cpp_lines)

# --- 3. Compiler & CLI Interface ---
def main():
    parser = argparse.ArgumentParser(description="SScript 1.0-gitrc")
    parser.add_argument("file", nargs="?", help="The .ss source file")
    parser.add_argument("-r", "--run", action="store_true", help="Compile and run immediately")
    args = parser.parse_args()

    if not args.file:
        print("\033[1;34m◈ SScript 1.0-gitrc ◈\033[0m")
        print("Usage: python3 sscript.py <file.ss> [-r]")
        return

    source_path = args.file
    binary_name = source_path.rsplit('.', 1)[0]
    temp_cpp = f"_{binary_name}_tmp.cpp"

    try:
        with open(source_path, "r") as f:
            ss_content = f.read()

        # Step 1: Transpile to C++
        cpp_output = transpile(ss_content)
        with open(temp_cpp, "w") as f:
            f.write(cpp_output)

        # Step 2: Compile to Binary using g++
        print(f"🔨 Compiling {source_path}...")
        compile_cmd = ["g++", "-O2", temp_cpp, "-o", binary_name]
        result = subprocess.run(compile_cmd)

        if result.returncode == 0:
            print(f"\033[1;32m✔ Created binary: ./{binary_name}\033[0m")
            
            # Step 3: Optional Execution
            if args.run:
                print(f"🚀 Running {binary_name}...")
                subprocess.run([f"./{binary_name}"])
        else:
            print("\033[1;31m✖ Compilation failed.\033[0m")

    finally:
        # Step 4: Cleanup temporary C++ file
        if os.path.exists(temp_cpp):
            os.remove(temp_cpp)

if __name__ == "__main__":
    main()
