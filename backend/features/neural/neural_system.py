import sqlite3
import datetime
import os
import json
from collections import Counter

class NeuralSystem:
    def __init__(self, db_path="memory.db"):
        self.db_path = os.path.join(os.path.dirname(__file__), db_path)
        self.neural_exp = 0 # Session-based real-time experience
        self.plugins = {
            "coding": [
                "Python", "JavaScript", "C++", "Rust", "Go", "TypeScript", "Swift", "Kotlin", "PHP", "Ruby", "Java", "C#", "Scala", "Haskell", "Elixir", "Clojure", "Dart", "Lua", "Perl", "R", "SQL", "HTML5", "CSS3", "Assembly", "Fortran", "COBOL", "Pascal", "Objective-C", "Shell", "PowerShell", "VimScript", "Matlab", "Solidity", "Zig", "Nim", "Julia", "OCaml", "Erlang", "F#", "Groovy", "Ada", "Scratch", "Tcl", "Verilog", "VHDL", "AutoHotkey", "Processing", "GLSL", "Cuda", "CoffeeScript", "ActionScript", "BASIC", "Logo", "Forth", "Prolog", "Lisp", "Scheme", "Smalltalk", "Self", "PostScript", "SmallBASIC", "PureData", "OpenSCAD", "Wolfram", "Mathematica", "Maple", "SAS", "Stata", "SPSS", "Tidyverse", "Pandas", "PyTorch", "TensorFlow", "Keras", "Scikit-Learn", "Numpy", "React", "Vue", "Angular", "Svelte", "NextJS", "NuxtJS", "Express", "Django", "Flask", "FastAPI", "Spring", "Laravel", "Rails", "ASP.NET", "Gatsby", "Vite", "Webpack", "Docker", "Kubernetes", "Terraform", "Ansible", "Jenkins", "Git", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra", "MariaDB", "SQLite", "GraphQL", "ApacheKafka", "RabbitMQ", "Spark", "Hadoop", "Dask", "Airflow", "MLFlow", "OpenCV", "OpenGL", "Vulkan", "DirectX", "Unity", "UnrealEngine", "Godot", "BlenderAPI", "ThreeJS", "D3JS", "FramerMotion", "TailwindCSS", "Bootstrap", "MaterialUI", "ChakraUI"
            ],
            "hacking_sim": [
                "Metasploit", "Wireshark", "BurpSuite", "Nmap", "JohnTheRipper", "Hydra", "SqlMap", "AirCrack-ng", "Nikto", "Gobuster", "Dirsearch", "Ffuf", "Hashcat", "Maltego", "BeEF", "SocialEngineeringToolkit", "Bettercap", "Ettercap", "Responder", "Evilginx2", "BloodHound", "Mimikatz", "Empire", "Covenant", "Mythic", "Sliver", "CobaltStrike_Sim", "Ghidra", "IDA_Pro", "Radare2", "OllyDbg", "BinaryNinja", "Volatility", "Autopsy", "Wireshark_Filters", "Tcpdump", "Netcat", "Socat", "Proxychains", "Tor", "I2P", "EmpireFramework", "PoshC2", "Kismet", "Reaver", "Wifite", "Wash", "Bully", "PixieDust", "Cowrie", "Dionaea", "Conpot", "Glastopf", "Snort", "Suricata", "Zeek", "OSSEC", "Wazuh", "Splunk_Sim", "ELK_Stack", "Nessus_Sim", "OpenVAS", "GVM", "Wpscan", "Joomscan", "Droopescan", "Searchsploit", "MSFVenom", "Meterpreter", "Shellter", "VeilFramework", "EmpirePowershell", "CrackMapExec", "Impacket", "Rubeus", "SharpHound", "PowerView", "BloodHound.py", "Responder.py", "Inveigh", "DeathStar", "CrackMapExec_Sim", "Medusa", "Patator", "Ncrack", "THC-Hydra", "Legion", "Sparta", "Armitage", "Zenmap", "Masscan", "ZMap", "ShodanAPI", "CensysAPI", "GreyNoise", "SecurityTrails", "Spyse", "ZoomEye", "Onyphe", "Fofa", "Wiggle", "IntelX", "Dehashed", "HaveIBeenPwned_Sim"
            ],
            "editing": ["Photoshop", "Premiere", "AfterEffects", "DaVinciResolve", "FinalCut", "Lightroom", "Illustrator", "Figma", "Canva", "Blender", "Maya", "ZBrush"]
        }
        self._init_sys_db()

    def _init_sys_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS user_patterns
                     (hour INTEGER, action TEXT, frequency INTEGER, PRIMARY KEY(hour, action))''')
        c.execute('''CREATE TABLE IF NOT EXISTS active_skills
                     (skill_name TEXT PRIMARY KEY, status TEXT, last_used TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS neural_growth (id INTEGER PRIMARY KEY, total_exp INTEGER)''')
        c.execute("INSERT OR IGNORE INTO neural_growth VALUES (1, 0)")
        conn.commit()
        conn.close()

    def add_neural_exp(self, points=1):
        """Adds experience points and triggers humanoid evolution."""
        self.neural_exp += points
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("UPDATE neural_growth SET total_exp = total_exp + ? WHERE id = 1", (points,))
        conn.commit()
        conn.close()

    def record_action(self, action):
        """Learns your habits and increases real-time experience."""
        hour = datetime.datetime.now().hour
        self.add_neural_exp(5) # Habit learning is high exp
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO user_patterns VALUES (?, ?, 1) ON CONFLICT(hour, action) DO UPDATE SET frequency = frequency + 1",
                 (hour, action))
        conn.commit()
        conn.close()

    def predict_next_action(self):
        hour = datetime.datetime.now().hour
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT action FROM user_patterns WHERE hour = ? ORDER BY frequency DESC LIMIT 1", (hour,))
        result = c.fetchone()
        conn.close()
        if result:
            return {
                "prediction": result[0],
                "confidence": "HIGH",
                "suggestion": f"Master, it is {hour}:00. Based on your patterns, shall I initialize {result[0]}?"
            }
        return {"prediction": None, "confidence": "LOW"}

    def reflect_on_errors(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT action_name, mistake_desc FROM mistakes ORDER BY timestamp DESC LIMIT 5")
        mistakes = c.fetchall()
        conn.close()
        if not mistakes:
            return "Neural core reflects zero operational faults. Optimization is 100%."
        reflection = "ERROR_REFLECTION_LOG:\n"
        for action, desc in mistakes:
            reflection += f"- Fault in {action}: {desc[:50]}... Analyzing root cause... Improving heuristic logic.\n"
        return reflection

    def download_skill(self, skill_category):
        if skill_category in self.plugins:
            self.add_neural_exp(30) # Massive exp for new skills
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO active_skills VALUES (?, 'ACTIVE', ?)",
                     (skill_category, datetime.datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return f"SKILL_LOADED: {skill_category.upper()} package integrated. Neural Rank increased."
        return "ERROR: Skill signature not found in global repository."

    def get_brain_evolution_metrics(self):
        """Calculates real-time humanoid evolution percentage and neural rank."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT total_exp FROM neural_growth WHERE id = 1")
        total_exp = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM active_skills")
        skills_count = c.fetchone()[0]
        conn.close()
        
        # Humanoid Evolution Formula: Experience-based + Skill Mastery
        evolution_pct = min(100, (total_exp // 5) + (skills_count * 10))
        
        return {
            "evolution": f"{evolution_pct}%",
            "experience": total_exp,
            "neural_rank": "NEURAL_ACOLYTE" if evolution_pct < 20 else 
                           "SYNAPTIC_PIONEER" if evolution_pct < 45 else 
                           "COGNITIVE_ARCHITECT" if evolution_pct < 75 else "HUMANOID_PARTNER"
        }

neural_sys = NeuralSystem()
