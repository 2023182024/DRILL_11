from pico2d import *
from transitions import Machine
import time

class Boy:
    SCREEN_WIDTH = 800
    SPRITE_WIDTH = 100
    MIN_X = SPRITE_WIDTH // 2
    MAX_X = SCREEN_WIDTH - SPRITE_WIDTH // 2

    states = ['IDLE', 'WALK', 'RUN', 'SLEEP', 'AUTORUN']

    def __init__(self):
        self.x, self.y = 400, 90
        self.frame = 0
        self.face_dir = 1
        self.image = load_image('animation_sheet.png')
        self.right_pressed = False
        self.left_pressed = False
        self.shift_keys_pressed = set()
        self.last_control_time = time.monotonic()
        self.autorun_start_time = None

        self.cursor=300
        state_transitions = [
            {'trigger': 'start_walk', 'source': ['IDLE', 'RUN', 'AUTORUN'], 'dest': 'WALK'},
            {'trigger': 'start_run', 'source': ['IDLE', 'WALK', 'AUTORUN'], 'dest': 'RUN'},
            {'trigger': 'stop_moving', 'source': ['WALK', 'RUN', 'AUTORUN'], 'dest': 'IDLE'},
            {'trigger': 'fall_asleep', 'source': 'IDLE', 'dest': 'SLEEP'},
            {'trigger': 'wake_up', 'source': 'SLEEP', 'dest': 'IDLE'},
            # AUTORUN entry (aliases)
            {'trigger': 'start_autorun', 'source': '*', 'dest': 'AUTORUN'},
            {'trigger': 'start_auto_run', 'source': '*', 'dest': 'AUTORUN'},
            {'trigger': 'auto_run', 'source': '*', 'dest': 'AUTORUN'},
            {'trigger': 'autorun', 'source': '*', 'dest': 'AUTORUN'},
            # AUTORUN exit (aliases)
            {'trigger': 'stop_autorun', 'source': 'AUTORUN', 'dest': 'IDLE'},
            {'trigger': 'finish_autorun', 'source': 'AUTORUN', 'dest': 'IDLE'},
            {'trigger': 'end_autorun', 'source': 'AUTORUN', 'dest': 'IDLE'},
            {'trigger': 'to_idle', 'source': 'AUTORUN', 'dest': 'IDLE'},
        ]
        self.machine = Machine(
            model=self,
            states=Boy.states,
            transitions=state_transitions,
            initial='IDLE',
            auto_transitions=False,
        )

    def handle_keydown(self, key):
        self.last_control_time = time.monotonic()
        if key == SDLK_RIGHT:
            self.face_dir=1
            self.right_pressed = True
        elif key==SDLK_LEFT:
            self.face_dir=2
            self.left_pressed=True
        elif key in (SDLK_LSHIFT, SDLK_RSHIFT):
            self.shift_keys_pressed.add(key)
        elif key in (SDLK_a, SDLK_SPACE, SDLK_RETURN, SDLK_KP_ENTER):
            # enter AUTORUN
            try:
                self.start_autorun()
            except Exception:
                pass
        self._sync_state_with_input()

    def handle_keyup(self, key):
        self.last_control_time = time.monotonic()
        if key == SDLK_RIGHT:
            self.right_pressed = False
        if key == SDLK_LEFT:
            self.left_pressed = False
        elif key in (SDLK_LSHIFT, SDLK_RSHIFT):
            self.shift_keys_pressed.discard(key)
        self._sync_state_with_input()

    def _sync_state_with_input(self):
        if self.state == 'SLEEP':
            self.wake_up()

        if self.state == 'AUTORUN':
            # arrow key -> RUN
            if self.right_pressed or self.left_pressed:
                try:
                    self.start_run()
                except Exception:
                    pass
                return

        if (self.right_pressed or self.left_pressed) and self.shift_keys_pressed:
            if self.state != 'RUN':
                self.start_run()
        elif self.right_pressed or self.left_pressed:
            if self.state != 'WALK':
                self.start_walk()
        elif self.state in ('WALK', 'RUN'):
            self.stop_moving()

    def update(self):
        if self.state == 'AUTORUN':
            if self.autorun_start_time is None:
                self.autorun_start_time = time.monotonic()

            # move 30 per frame in x direction
            self.x += -30 if self.face_dir == 2 else 30

            # boundary bounce
            if self.x <= self.MIN_X:
                self.x = self.MIN_X
                self.face_dir = 1
            elif self.x >= self.MAX_X:
                self.x = self.MAX_X
                self.face_dir = 2

            # 5 seconds -> IDLE
            if time.monotonic() - self.autorun_start_time >= 5:
                for trig in ('stop_autorun', 'finish_autorun', 'end_autorun', 'to_idle', 'stop_moving'):
                    try:
                        getattr(self, trig)()
                        break
                    except Exception:
                        continue
        else:
            self.autorun_start_time = None

            if self.state == 'WALK':
                self.x += -5 if self.face_dir == 2 else 5
            elif self.state == 'RUN':
                self.x += -15 if self.face_dir == 2 else 15

        self.x = min(max(self.x, self.MIN_X), self.MAX_X)

        self.frame = (self.frame + 1) % 8
        if self.state == 'IDLE' and time.monotonic() - self.last_control_time >= 30:
            self.fall_asleep()

    def draw(self):
        size = 200 if self.state == 'AUTORUN' else 100

        if self.state=='RUN' or self.state == 'WALK' or self.state == 'AUTORUN':
            if self.face_dir == 2:
                self.cursor=0
            else:
                self.cursor=1
        else:
            if self.face_dir == 2:
                self.cursor=2
            else:
                self.cursor=3

        if self.state=='SLEEP':
            self.image.clip_composite_draw(self.frame * 100,self.cursor*100, 100, 100,math.radians(90),'', self.x, self.y-20,size,size)
        else:
            self.image.clip_draw(self.frame * 100,self.cursor*100, 100, 100, self.x, self.y, size, size)