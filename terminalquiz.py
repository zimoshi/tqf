import curses
import threading
import time
import random

class LoadingBar:
    def __init__(self, length, initial_percentage=0):
        self.percentage = initial_percentage
        self.bar_length = length  # Number of '━' characters in the bar

    def printlb(self):
        filled_length = int(self.percentage / 100 * self.bar_length)
        filled_bar = "\033[38;5;125m━\033[0m" * filled_length  # Purple for filled
        unfilled_bar = "\033[38;5;046m━\033[0m" * (self.bar_length - filled_length - 1)  # Green for unfilled
        bar = filled_bar + " " + unfilled_bar  # Combine filled, separator, and unfilled
        pc = f"\033[38;5;021m{self.percentage}%\033[0m"
        print(f"\r{bar} {pc}", end="\n", flush=True)

    def increase(self, value):
        self.percentage = min(100, self.percentage + value)
        self.printlb()

    def decrease(self, value):
        self.percentage = max(0, self.percentage - value)
        self.printlb()

class TerminalQuiz:
    def __init__(self, title, time_limit=10):
        self.title = title
        self.questions = []
        self.current = 0
        self.score = 0
        self.time_limit = time_limit
        self.timeout = False
        self.running = True
        self.timer_thread = None
        self.timer_cancel = threading.Event()
        self.remaining = self.time_limit
        self.screen = None
        self.skipped_questions = []

    def add_question(self, question, choices, answer):
        self.questions.append({
            "question": question,
            "choices": choices,
            "answer": answer,
            "skipped": False,
        })

    def draw_full_screen(self):
        self.screen.clear()

        if self.current >= len(self.questions):
            self.screen.addstr(2, 2, f"Quiz completed. Final Score: {self.score}/{len(self.questions)}")
            if self.skipped_questions:
                self.screen.addstr(4, 2, "Skipped Questions:")
                for idx, question in enumerate(self.skipped_questions):
                    self.screen.addstr(6 + idx, 4, f"- {question}")
            self.running = False
            self.screen.refresh()
            return

        q = self.questions[self.current]

        self.screen.addstr(0, 2, f"{self.title}   [Score: {self.score}]  [Option+Cmd+E to Exit]")

        if self.remaining <= 5:
            self.screen.attron(curses.color_pair(1))
        self.screen.addstr(1, 2, f"(You have {self.remaining} seconds)")
        if self.remaining <= 5:
            self.screen.attroff(curses.color_pair(1))

        self.screen.addstr(3, 2, q["question"])
        for idx, choice in enumerate(q["choices"]):
            letter = chr(65 + idx)
            self.screen.addstr(5 + idx, 4, f"({letter}) {choice}")

        self.screen.addstr(8, 2, "[Option+Cmd+S to Skip]")
        self.screen.refresh()

    def next_question(self):
        self.timer_cancel.set()
        if self.timer_thread and self.timer_thread.is_alive() and threading.current_thread() != self.timer_thread:
            self.timer_thread.join()

        self.current += 1
        self.remaining = self.time_limit
        if self.current >= len(self.questions):
            self.running = False
        else:
            self.draw_full_screen()
            self.start_timer()

    def skip_question(self, timeout=False):
        self.timer_cancel.set()
        if self.timer_thread and self.timer_thread.is_alive() and threading.current_thread() != self.timer_thread:
            self.timer_thread.join()

        if self.current < len(self.questions):
            if timeout:
                self.screen.addstr(10, 2, "\u23f1\ufe0f  Time's up! Skipping...")
                self.screen.addstr(11, 2, "\a")  # Beep
            self.questions[self.current]["skipped"] = True
            self.skipped_questions.append(self.questions[self.current]["question"])
        self.next_question()

    def live_countdown(self):
        while self.remaining > 0 and not self.timer_cancel.is_set() and self.running:
            self.draw_full_screen()
            time.sleep(1)
            self.remaining -= 1
        if not self.timer_cancel.is_set() and self.running:
            self.timeout = True

    def start_timer(self):
        self.timeout = False
        self.timer_cancel.clear()

        self.timer_thread = threading.Thread(target=self.live_countdown)
        self.timer_thread.daemon = True
        self.timer_thread.start()

        while not self.timeout and self.running:
            key = self.screen.getch()
            if key == 19:  # Ctrl+S (skip)
                self.timer_cancel.set()
                if self.timer_thread and self.timer_thread.is_alive() and threading.current_thread() != self.timer_thread:
                    self.timer_thread.join()
                self.skip_question()
                break
            elif key == 5:  # Ctrl+E (exit)
                self.timer_cancel.set()
                if self.timer_thread and self.timer_thread.is_alive() and threading.current_thread() != self.timer_thread:
                    self.timer_thread.join()
                self.running = False
                break
            elif key in range(65, 91) or key in range(97, 123):  # A-Z or a-z
                self.timer_cancel.set()
                if self.timer_thread and self.timer_thread.is_alive() and threading.current_thread() != self.timer_thread:
                    self.timer_thread.join()
                self.check_answer(chr(key).upper())
                break

        if self.timeout and self.running:
            self.skip_question(timeout=True)

    def check_answer(self, selected):
        correct = self.questions[self.current]["answer"]
        if selected == correct:
            self.screen.addstr(10, 2, "\u2705 Correct!")
            self.score += 1
        else:
            self.screen.addstr(10, 2, f"\u274c Incorrect. Correct answer was {correct}.")
        self.screen.refresh()
        time.sleep(1)
        self.next_question()

    def run(self):
        curses.wrapper(self._run)

    def _run(self, screen):
        self.screen = screen
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        self.screen.clear()
        random.shuffle(self.questions)
        self.draw_full_screen()
        self.start_timer()

RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
BLUE = "\033[34m"
BOLD = "\033[1m"
YELLOW = "\033[33m"
import time,os

# Initialize a LoadingBar with max length 100 and starting percentage 0
lb = LoadingBar(100, 0)

# Simulate progress
for i in range(100):
    os.system('cls' if os.name == 'nt' else 'clear')  # Clear the console
    print(f"""
{RED}+++++++{RESET}   {GREEN}++++++{RESET}    {BLUE}+++++++{RESET}
   {RED}+{RESET}     {GREEN}+     +{RESET}    {BLUE}+{RESET}      
   {RED}+{RESET}    {GREEN}+       +{RESET}   {BLUE}+{RESET}      
   {RED}+{RESET}    {GREEN}+   +   +{RESET}   {BLUE}++++{RESET}   
   {RED}+{RESET}    {GREEN}+    ++++{RESET}   {BLUE}+{RESET}      
   {RED}+{RESET}     {GREEN}+++++ +{RESET}    {BLUE}+{RESET}      
               {GREEN}+{RESET}           
{BOLD}{YELLOW}TQF - Make quizzes work{RESET}
{BOLD}{GREEN}Terminal Quiz Framework is loading...{RESET}
    """)
    lb.increase(1)  # Increment progress
    time.sleep(0.05)  # Delay for demonstration

print(f"{BOLD}TQF load complete!{RESET}")

del LoadingBar,lb,time,os # Clean up the namespace