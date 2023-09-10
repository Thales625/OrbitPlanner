from PySimpleGUI import PySimpleGUI as sg
import pygame as pg
from threading import Thread
from math import ceil

from Vector import Vector2, Vector3

G = 6.674080324960551e-11

def vec3_ignore_z(VEC3):
    return Vector2(VEC3.x, VEC3.y)

class Body:
    def __init__(self, name, pos, mass, radius) -> None:
        self.name = name
        self.pos = pos
        self.mass = mass
        self.radius = radius
        self.GM = G * self.mass

def get_body_by_name(body_name):
    for body in bodies:
        if body.name == body_name:
            return body
    return False

def rk4(pos):
    accel = Vector3()

    for body in bodies:
        delta_pos = body.pos - pos
        dist = delta_pos.magnitude()
        direction = delta_pos / dist

        accel += (body.GM/dist**2) * direction # gravity

    return accel

def calc(r0, v0, total_time):
    r = [r0]
    v = [v0]

    steps = ceil(total_time / step_size)

    for step in range(steps):
        print(f"SIM: {(step/steps * 100):.0f}%")

        k1v = rk4(r[-1])
        k1r = v[-1]

        k2v = rk4(r[-1]+k1r*step_size*.5)
        k2r = v[-1]+k1v*step_size*.5

        k3v = rk4(r[-1]+k2r*step_size*.5)
        k3r = v[-1]+k2v*step_size*.5

        k4v = rk4(r[-1]+k3r*step_size)
        k4r = v[-1]+k3v*step_size

        dv = (step_size/6)*(k1v + 2*k2v + 2*k3v + k4v)
        dr = (step_size/6)*(k1r + 2*k2r + 2*k3r + k4r)

        v.append(v[-1] + dv)
        r.append(r[-1] + dr)

    return r, v

def update_screen():
    screen.blit(surface_enviroment, (0, 0))
    screen.blit(surface_manuever, (0, 0))
    pg.display.update()

def render_manuever():
    surface_manuever.fill((0, 0, 0, 0))

    for i in range(len(manuever_r)-1): # manuever trajectory
        a = manuever_r[i]
        b = manuever_r[i+1]
        pg.draw.line(surface_manuever, (0, 255, 0), camera_pos + vec3_ignore_z(a)*scale, camera_pos + vec3_ignore_z(b)*scale)
    pg.draw.circle(surface_manuever, (100, 100, 100), camera_pos + vec3_ignore_z(r[manuever_index])*scale, 5)
        
def render_enviroment():
    surface_enviroment.fill("#3C3846")

    for body in bodies: # draw bodies
        pg.draw.circle(surface_enviroment, (0, 0, 100), camera_pos + vec3_ignore_z(body.pos)*scale, body.radius*scale)

    for i in range(len(r)-1): # draw main trajectory
        a = r[i]
        b = r[i+1]
        pg.draw.line(surface_enviroment, (255, 0, 0), camera_pos + vec3_ignore_z(a)*scale, camera_pos + vec3_ignore_z(b)*scale)

def mouse_down_handler(pos):
    global manuever_index

    # set index on click
    if len(r) == 0: return
    min_index = 0
    min_dist = 9999999
    for i, p in enumerate(r):
        p_2d = camera_pos + vec3_ignore_z(p)*scale
        dist = (Vector2(pos) - p_2d).magnitude()
        if dist < min_dist:
            min_dist = dist
            min_index = i
    update_man_index(min_index)
    render_manuever()
    update_screen()

def key_down_handler(key):
    global scale, camera_pos

    if key == pg.K_KP_PLUS or key == pg.K_PLUS:
        scale += delta_scale
        render_enviroment()
        update_screen()
        return
    if key == pg.K_KP_MINUS or key == pg.K_MINUS:
        scale -= delta_scale
        render_enviroment()
        update_screen()
        return
    if key == pg.K_UP:
        camera_pos.y += camera_speed
        render_enviroment()
        update_screen()
        return
    if key == pg.K_DOWN:
        camera_pos.y -= camera_speed
        render_enviroment()
        update_screen()
        return
    if key == pg.K_RIGHT:
        camera_pos.x -= camera_speed
        render_enviroment()
        update_screen()
        return
    if key == pg.K_LEFT:
        camera_pos.x += camera_speed
        render_enviroment()
        update_screen()
        return
    
    if key == pg.K_KP_ENTER or key == 13:
        print("MANUEVER RUNNING...")
        global manuever_r, manuever_v

        tg = manuever_vel.x
        m_vel = v[manuever_index].normalize() * tg

        manuever_r, manuever_v = calc(r[manuever_index], v[manuever_index] + m_vel, manuever_time)
        render_manuever()
        update_screen()
        return

def controller_event_handler(event, values):
    global step_size, total_time, manuever_time

    steps = values.copy()

    for key, value in steps.items():
        try:
            steps[key] = int(value)
        except (ValueError, TypeError):
            steps[key] = 1

    # SIMULATION
    if event == "add_sim-step-size":
        step_size += steps["step_sim-step-size"]
        window_controller["display_sim-step-size"].update(step_size)
        return
    if event == "sub_sim-step-size":
        step_size -= steps["step_sim-step-size"]
        window_controller["display_sim-step-size"].update(step_size)
        return
    if event == "add_sim-time":
        total_time += steps["step_sim-time"]
        window_controller["display_sim-time"].update(total_time)
        return
    if event == "sub_sim-time":
        total_time -= steps["step_sim-time"]
        window_controller["display_sim-time"].update(total_time)
        return
    if event == "btn_sim-exec":
        global r, v
        r, v = calc(p0, v0, total_time)
        render_enviroment()
        update_screen()
        return
    
    # MANUEVER
    if event == "add_man-time":
        manuever_time += steps["step_man-time"]
        window_controller["display_man-time"].update(manuever_time)
        return
    if event == "sub_man-time":
        manuever_time -= steps["step_man-time"]
        window_controller["display_man-time"].update(manuever_time)
        return
    if event == "add_man-index":
        update_man_index(manuever_index + steps["step_man-index"])
        return
    if event == "sub_man-index":
        update_man_index(manuever_index - steps["step_man-index"])
        return
    
    # VEL
    if event == "add_man-vel-tg":
        manuever_vel.x += steps["step_man-vel-tg"]
        window_controller["display_man-vel-tg"].update(manuever_vel.x)
        return
    if event == "add_man-vel-norm":
        manuever_vel.y += steps["step_man-vel-norm"]
        window_controller["display_man-vel-norm"].update(manuever_vel.y)
        return
    if event == "add_man-vel-rad":
        manuever_vel.z += steps["step_man-vel-rad"]
        window_controller["display_man-vel-rad"].update(manuever_vel.z)
        return
    
    if event == "sub_man-vel-tg":
        manuever_vel.x -= steps["step_man-vel-tg"]
        window_controller["display_man-vel-tg"].update(manuever_vel.x)
        return
    if event == "sub_man-vel-norm":
        manuever_vel.y -= steps["step_man-vel-norm"]
        window_controller["display_man-vel-norm"].update(manuever_vel.y)
        return
    if event == "sub_man-vel-rad":
        manuever_vel.z -= steps["step_man-vel-rad"]
        window_controller["display_man-vel-rad"].update(manuever_vel.z)
        return
    
    # NODE CREATION
    if event == "add_man-node":
        manuever_nodes.append([sg.Text("NODE")])
        window_controller["dynamic_column-node"].update([manuever_nodes])
        #window_controller.extend_layout(window_controller["dynamic_column-node"], [[sg.Text("NODE")]])
        #print(len(manuever_nodes))
        return
    
    # MANUEVER EXEC
    if event == "btn_man-exec":
        global manuever_v, manuever_r
        man_vel = v[manuever_index].normalize() * manuever_vel.x
        manuever_r, manuever_v = calc(r[manuever_index], v[manuever_index] + man_vel, manuever_time)
        render_manuever()
        update_screen()

def update_man_index(index):
    global manuever_index
    if index < 0 or index >= len(r) or index == manuever_index: return
    manuever_index = index
    window_controller["display_man-index"].update(index)
    render_manuever()
    update_screen()

bodies = []
with open("bodies.txt", "r") as file: # load bodies
    for line in file.readlines()[1:]:
        name, pos, mass, radius = line.replace("\n", "").split("|")
        pos = Vector3(eval(pos))
        pos.z = 0 # remove height
        mass = float(mass)
        radius = int(radius)
        bodies.append(Body(name, pos, mass, radius))
earth = get_body_by_name("Earth")

# RK4
step_size = 50
total_time = 10000
manuever_time = 10000

# trajectory
r = []
v = []
p0 = earth.pos - Vector3(0, earth.radius+400000)
v0 = Vector3(7660, 0, 0)

# PG
screen_size = Vector2(800, 800)      
screen = pg.display.set_mode(screen_size)
pg.display.set_caption("Orbit")

surface_enviroment = pg.Surface(screen_size)
surface_manuever = pg.Surface(screen_size, pg.SRCALPHA)

camera_pos = screen_size * 0.5  
camera_speed = 10

delta_scale = 9e-7
scale = 15e-6

manuever_index = 0
manuever_scale = 10
manuever_vel = Vector3(0, 0, 0) # tg | norm | radial
manuever_r = []
manuever_v = []
manuever_nodes = []

# SG
font_size = lambda size: ("DS-Digital", size)
sg.theme("Dark")
sg.set_options(font=font_size(20))
layout = [
    [sg.Text("==SIMULATION==", font=font_size(48))],
    [sg.Text("Step Size"), sg.Text(str(step_size), key="display_sim-step-size", font=font_size(25)), sg.Button("+", key="add_sim-step-size"), sg.Button("-", key="sub_sim-step-size"), sg.InputText("1", size=(5, 1), key="step_sim-step-size")],
    [sg.Text("Time"), sg.Text(str(total_time), key="display_sim-time", font=font_size(25)), sg.Button("+", key="add_sim-time"), sg.Button("-", key="sub_sim-time"), sg.InputText("1", size=(5, 1), key="step_sim-time")],
    [sg.Button("Simulate", key="btn_sim-exec", font=font_size(28))],
    [sg.Text("==MANUEVER==", font=font_size(48))],
    [sg.Text("Index"), sg.Text(str(manuever_index), key="display_man-index", font=font_size(25)), sg.Button("+", key="add_man-index"), sg.Button("-", key="sub_man-index"), sg.InputText("1", size=(5, 1), key="step_man-index")],
    [sg.Text("Time"), sg.Text(str(manuever_time), key="display_man-time", font=font_size(25)), sg.Button("+", key="add_man-time"), sg.Button("-", key="sub_man-time"), sg.InputText("1", size=(5, 1), key="step_man-time")],
    [sg.Text("--Vel--")],
    [sg.Text("tg"), sg.Text(str(manuever_vel.x), key="display_man-vel-tg", font=font_size(25)), sg.Button("+", key="add_man-vel-tg"), sg.Button("-", key="sub_man-vel-tg"), sg.InputText("1", size=(5, 1), key="step_man-vel-tg")],
    [sg.Text("norm"), sg.Text(str(manuever_vel.y), key="display_man-vel-norm", font=font_size(25)), sg.Button("+", key="add_man-vel-norm"), sg.Button("-", key="sub_man-vel-norm"), sg.InputText("1", size=(5, 1), key="step_man-vel-norm")],
    [sg.Text("rad"), sg.Text(str(manuever_vel.z), key="display_man-vel-rad", font=font_size(25)), sg.Button("+", key="add_man-vel-rad"), sg.Button("-", key="sub_man-vel-rad"), sg.InputText("1", size=(5, 1), key="step_man-vel-rad")],
    [sg.Button("Execute Manuever", key="btn_man-exec")],
]
window_controller = sg.Window("Controller", layout)
'''[sg.Text("--Create Node--")],
    [sg.Button("+", key="add_man-node"), sg.Button("-", key="sub_man-node")],
    [sg.Text("-----Nodes-----")],
    [sg.Column([], key="dynamic_column-node")],
    [sg.Text("---------------")]'''
render_enviroment()
update_screen()

while True:
    # PG - Renderer
    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.quit()
            break
        if event.type == pg.KEYDOWN:
            key_down_handler(event.key)
        elif event.type == pg.MOUSEBUTTONDOWN:
            mouse_down_handler(pg.mouse.get_pos())

    # SG - Controller
    event, values = window_controller.read(timeout=100)
    
    if event == sg.WIN_CLOSED:
        pg.quit()
        break
    
    if event is not None: controller_event_handler(event, values)