import cv2
import numpy as np
from pynput.keyboard import Controller
from input_zone import InputZone
from input_mode import InputModes
from input_group import InputGroup
from config import SaveManager, SaveData

save_manager = SaveManager()
window_name = "Motion Control"
keyboard = Controller()
cap = cv2.VideoCapture(0)
background = None
zones: list[InputZone] = []
mouse_pos = (0, 0)
current_mode = InputModes.DEFAULT
selected_zone: InputZone = None
initial_position = (0, 0)
selection_offset = (0, 0)
groups: list[InputGroup] = []


def load_config(file_path: str = None):
    global zones

    try:
        save_data = save_manager.load(file_path)
        zones = []
        for zone in save_data.zones:
            add_zone(zone)
    except Exception:
        print("Error while trying to load save data.")


def add_zone(zone: InputZone):
    zones.append(zone)
    add_to_group(zone)


def remove_zone(zone: InputZone):
    zones.remove(zone)
    remove_from_group(zone)


def add_to_group(zone: InputZone):
    if zone.group is None:
        return

    for group in groups:
        if group.id == zone.group:
            group.add_zone(zone)
            return

    new_group = InputGroup(zone.group)
    new_group.add_zone(zone)
    groups.append(new_group)


def remove_from_group(zone: InputZone):
    if zone.group is None:
        return

    for group in groups:
        if group.id == zone.group:
            group.remove_zone(zone)
            return


def find_group(id):
    for group in groups:
        if group.id == id:
            return group
    return None


def create_zone(x, y):
    new_zone = InputZone(x, y, x + 50, y + 50, key=None, inverted=False)
    add_zone(new_zone)


def invert_zone(x, y):
    for z in zones:
        if z.x1 < x < z.x2 and z.y1 < y < z.y2:
            z.inverted = not z.inverted


def destroy_zone(x, y):
    for z in zones:
        if z.x1 < x < z.x2 and z.y1 < y < z.y2:
            remove_zone(z)


def select_zone(x, y):
    global selected_zone, initial_position, selection_offset
    for z in zones:
        if z.x1 < x < z.x2 and z.y1 < y < z.y2:
            selected_zone = z
            initial_position = (x, y)
            selection_offset = (x - z.x1, y - z.y1)
            break


def move_zone(x, y):
    if selected_zone is None:
        return

    selected_zone.set_position(
        x - selection_offset[0], y - selection_offset[1])


def resize_zone(x, y):
    if selected_zone is None:
        return

    w = x - initial_position[0] + selection_offset[0]
    h = y - initial_position[1] + selection_offset[1]
    selected_zone.set_size(w, h)


def set_key(x, y, key):
    for z in zones:
        if z.x1 < x < z.x2 and z.y1 < y < z.y2:
            z.key = chr(key)
            break


def set_group(x, y, group):
    for z in zones:
        if z.x1 < x < z.x2 and z.y1 < y < z.y2:
            remove_from_group(z)
            z.group = group
            add_to_group(z)
            break


def set_priority(x, y, priority):
    for z in zones:
        if z.x1 < x < z.x2 and z.y1 < y < z.y2:
            z.priority = priority
            break


def calc_diff(frame1, frame2):
    base_bright = frame2.mean()
    curr_bright = frame1.mean()
    frame1 = cv2.convertScaleAbs(
        frame1, alpha=1, beta=base_bright - curr_bright)
    diff = cv2.absdiff(frame2, frame1)
    _, thresh = cv2.threshold(diff, 35, 255, cv2.THRESH_BINARY)
    return thresh


def apply_filters(frame):
    res = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    res = cv2.GaussianBlur(res, (5, 5), 0)
    return res


def test_zones(zones: list[InputZone], diff):
    for z in zones:
        zone_diff = diff[z.y1:z.y2, z.x1:z.x2]

        triggered = np.sum(zone_diff) > 10000
        if z.inverted:
            triggered = not triggered
        if triggered:
            activate_zone(z)
        else:
            deactivate_zone(z)


def draw_zones(frame, zones: list[InputZone]):
    for z in zones:
        active_color = (0, 0, 255) if z.pressed else (255, 0, 0)
        inactive_color = (0, 255, 255) if z.inverted else (255, 255, 0)

        cv2.rectangle(frame, (z.x1, z.y1), (z.x2, z.y2),
                      inactive_color if background is None else active_color, 2)
        cv2.putText(frame, f"{z.key}", (z.x1 + 5, z.y2 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        if z.group is not None:
            cv2.putText(frame, f"{z.group}-{z.priority}", (z.x1 + 5, z.y1 + 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)


def mouse_event(event, x, y, flags, param):
    global mouse_pos, selected_zone
    if event == cv2.EVENT_MOUSEMOVE:
        mouse_pos = (x, y)
        if current_mode == InputModes.MOVE:
            move_zone(x, y)
        elif current_mode == InputModes.RESIZE:
            resize_zone(x, y)

    elif event == cv2.EVENT_LBUTTONDOWN:
        select_zone(x, y)
    elif event == cv2.EVENT_LBUTTONUP:
        selected_zone = None


def key_pressed(key):
    if key == -1:
        return

    global current_mode, background

    if current_mode == InputModes.SET_KEY:
        current_mode = InputModes.DEFAULT
        set_key(mouse_pos[0], mouse_pos[1], key)
        return
    elif current_mode == InputModes.GROUP:
        current_mode = InputModes.DEFAULT
        try:
            set_group(mouse_pos[0], mouse_pos[1], int(chr(key)))
        except ValueError:
            print("Not a valid group number")
        return
    elif current_mode == InputModes.PRIORITY:
        current_mode = InputModes.DEFAULT
        try:
            set_priority(mouse_pos[0], mouse_pos[1], int(chr(key)))
        except ValueError:
            print("Not a valid group number")
        return

    if key == ord("1"):
        current_mode = InputModes.DEFAULT
    elif key == ord("2"):
        create_zone(mouse_pos[0], mouse_pos[1])
    elif key == ord("3"):
        destroy_zone(mouse_pos[0], mouse_pos[1])
    elif key == ord("4"):
        current_mode = InputModes.MOVE
    elif key == ord("5"):
        current_mode = InputModes.RESIZE
    elif key == ord("6"):
        current_mode = InputModes.SET_KEY
    elif key == ord("7"):
        invert_zone(mouse_pos[0], mouse_pos[1])
    elif key == ord("8"):
        current_mode = InputModes.GROUP
    elif key == ord("9"):
        current_mode = InputModes.PRIORITY
    elif key == ord("-"):
        load_config()
    elif key == ord("="):
        save_manager.save(SaveData(zones))
    elif key == 13:
        background = apply_filters(frame) if background is None else None
        current_mode = InputModes.DEFAULT


def draw_current_mode():
    text = f"{current_mode} - {"Active" if background is not None else "Inactive"}"
    color = (255, 255, 255) if background is not None else (0, 0, 255)
    cv2.putText(frame, text, (0, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)


def draw_frame():
    pass


def can_activate(zone: InputZone):
    if zone.group is None:
        return True

    can_activate = True
    group = find_group(zone.group)
    for z in group.zones:
        if z == zone:
            continue
        if z.group == zone.group and z.priority > zone.priority and z.pressed:
            can_activate = False
            break

    return can_activate


def activate_zone(zone: InputZone):
    if zone.pressed or not can_activate(zone):
        return False

    if zone.key is not None:
        keyboard.press(zone.key)
    zone.pressed = True

    if zone.group is None:
        return

    group = find_group(zone.group)

    for z in group.zones:
        if z == zone:
            continue
        if z.group == zone.group and z.priority < zone.priority and z.pressed:
            deactivate_zone(z)


def deactivate_zone(zone: InputZone):
    if not zone.pressed:
        return

    if zone.key is not None:
        keyboard.release(zone.key)
    zone.pressed = False


cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.setMouseCallback(window_name, mouse_event)
if save_manager.get_last_save():
    load_config(save_manager.get_last_save())

while True:
    ret, frame = cap.read()
    if not ret:
        break

    key = cv2.waitKey(1)
    if key == 27:  # ESC pressed
        break

    frame = cv2.flip(frame, 1)

    key_pressed(key)

    if background is not None:
        prep_frame = apply_filters(frame)
        frames_diff = calc_diff(prep_frame, background)
        test_zones(zones, frames_diff)

    draw_zones(frame, zones)
    draw_current_mode()

    cv2.imshow(window_name, frame)

cap.release()
cv2.destroyAllWindows()
