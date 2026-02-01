import sys, os, subprocess, re, argparse, platform

# --- 1. SScript Core (Standard Library) ---
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
    std::string user() { return getenv("USER") ? getenv("USER") : "unknown"; }
    
    void notify(std::string t, std::string m) {
        std::string cmd = "notify-send \\""+t+"\\" \\""+m+"\\"";
        // (void) ignores the return value to silence compiler warnings
        (void)!system(cmd.c_str()); 
    }
}

namespace Net {
    // Fetches raw text from a URL
    void fetch(std::string url, std::string save_path) {
        std::string cmd = "curl -s " + url + " -o " + save_path;
        (void)!system(cmd.c_str());
    }

    // Opens a browser search
    void search(std::string query) {
        std::string cmd = "xdg-open https://www.google.com/search?q=" + query + " &";
        (void)!system(cmd.c_str());
    }
}
"""

# --- 2. Advanced Transpiler ---
def transpile(ss_code):
    lines = ss_code.splitlines()
    cpp_body = []
    has_main = any(re.search(r'\b(fn|int)\s+main\(', line) for line in lines)
    
    for line in lines:
        raw_line = line.strip()
        if not raw_line or raw_line.startswith("#"): continue
        
        # 1. Formatting print calls
        line = re.sub(r'print\((.*)\)', r'print(\1)', line)
        
        # 2. Syntax mapping
        line = re.sub(r'\bvar\b', 'auto', line)
        line = re.sub(r'\bfn\s+', 'void ', line)
        line = line.replace('void main()', 'int main()')
        
        # 3. Namespace conversion (Dot to Double-Colon)
        modules = ["Battery", "System", "File", "Media", "Hardware", "Net"]
        for mod in modules:
            line = line.replace(f"{mod}.", f"{mod}::")

        # 4. Auto-Semicolon logic
        clean = line.strip()
        if clean and not clean.endswith(('{', '}', ';', ':')):
            line += ";"
            
        cpp_body.append(line)

    body_content = "\n    ".join(cpp_body)
    if not has_main:
        return f"{CORE_HEADER}\nint main() {{\n    {body_content}\n    return 0;\n}}"
    return f"{CORE_HEADER}\n" + "\n".join(cpp_body)

# --- 3. Professional CLI Dashboard ---
def main():
    parser = argparse.ArgumentParser(description="SScript Compiler")
    parser.add_argument("file", nargs="?")
    parser.add_argument("-r", "--run", action="store_true")
    args = parser.parse_args()

    if not args.file:
        print("\033[1;32m◈ SScript Module Engine v1.0-rc ◈\033[0m")
        print("Modules: Battery, System, File, Media, Hardware, Net")
        return

    try:
        with open(args.file, "r") as f:
            cpp_content = transpile(f.read())
            
        with open("temp.cpp", "w") as f:
            f.write(cpp_content)

        output_bin = args.file.split('.')[0]
        # Added -w to suppress remaining minor warnings if they annoy you
        compile_cmd = ["g++", "-O2", "temp.cpp", "-o", output_bin]
        
        if subprocess.run(compile_cmd).returncode == 0:
            if args.run:
                subprocess.run([f"./{output_bin}"])
        
        if os.path.exists("temp.cpp"): os.remove("temp.cpp")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
