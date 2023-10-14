from PySimpleGUI import PySimpleGUI as sg
import pygame as pg
from itertools import combinations
from math import ceil

from Vector import Vector2, Vector3

"""
TODO
-Use combinations to calculate bodies trajectories
Ex: [Earth, Moon, Mars, Saturn] = [(Earth, Moon), (Earth, Mars), (Earth, Saturn), (Moon, Mars), (Moon, Saturn), (Mars, Saturn)]
-Trajectory
Create a class in other file
"""

G = 6.674080324960551e-11

def vec3_ignore_z(VEC3):
    return Vector2(VEC3.x, VEC3.y)

class Body:
    def __init__(self, name, r0, v0, mass, radius) -> None:
        self.name = name
        self.r0 = r0
        self.v0 = v0
        self.r = [self.r0]
        self.v = [self.v0]
        self.mass = mass
        self.radius = radius
        self.GM = G * self.mass

def get_body_by_name(body_name):
    for body in bodies:
        if body.name.lower() == body_name.lower():
            return body
    return False

def rk4_body(p, body):
    accel = Vector3(0, 0, 0)

    for other_body in bodies:
        if other_body is not body:
            delta_pos = other_body.r[-1] - p
            dist = delta_pos.magnitude()
            direction = delta_pos / dist

            accel += (other_body.GM/(dist**2)) * direction

    return accel

def rk4_vessel(p):
    accel = Vector3()

    for body in bodies:
        delta_pos = body.r[0] - p
        dist = delta_pos.magnitude()
        direction = delta_pos / dist

        accel += (body.GM/dist**2) * direction # gravity

    return accel

def calc_bodies():
    steps = ceil(body_sim_time / body_step_size)

    for body in bodies:
        body.r = [body.r0]
        body.v = [body.v0]

    for step in range(steps):
        for body in bodies:
            k1v = rk4_body(body.r[-1], body)
            k1r = body.v[-1]

            k2v = rk4_body(body.r[-1]+k1r*body_step_size*.5, body)
            k2r = body.v[-1]+k1v*body_step_size*.5

            k3v = rk4_body(body.r[-1]+k2r*body_step_size*.5, body)
            k3r = body.v[-1]+k2v*body_step_size*.5

            k4v = rk4_body(body.r[-1]+k3r*body_step_size, body)
            k4r = body.v[-1]+k3v*body_step_size

            dv = (body_step_size/6)*(k1v + 2*k2v + 2*k3v + k4v)
            dr = (body_step_size/6)*(k1r + 2*k2r + 2*k3r + k4r)

            body.v.append(body.v[-1] + dv)
            body.r.append(body.r[-1] + dr)

def calc_vessel(r0, v0, total_time):
    r = [r0]
    v = [v0]

    steps = ceil(total_time / vessel_step_size)

    for step in range(steps):
        #print(f"SIM: {(step/steps * 100):.0f}%")

        k1v = rk4_vessel(r[-1])
        k1r = v[-1]

        k2v = rk4_vessel(r[-1]+k1r*vessel_step_size*.5)
        k2r = v[-1]+k1v*vessel_step_size*.5

        k3v = rk4_vessel(r[-1]+k2r*vessel_step_size*.5)
        k3r = v[-1]+k2v*vessel_step_size*.5

        k4v = rk4_vessel(r[-1]+k3r*vessel_step_size)
        k4r = v[-1]+k3v*vessel_step_size

        dv = (vessel_step_size/6)*(k1v + 2*k2v + 2*k3v + k4v)
        dr = (vessel_step_size/6)*(k1r + 2*k2r + 2*k3r + k4r)

        v.append(v[-1] + dv)
        r.append(r[-1] + dr)

    return r, v

def update_screen():
    screen.blit(surface_enviroment, (0, 0))
    screen.blit(surface_maneuver, (0, 0))
    pg.display.update()

def render_maneuver():
    if len(r) == 0: return
    surface_maneuver.fill((0, 0, 0, 0))

    for i in range(len(maneuver_r)-1): # maneuver trajectory
        a = maneuver_r[i]
        b = maneuver_r[i+1]
        pg.draw.line(surface_maneuver, (0, 255, 0), camera_pos + vec3_ignore_z(a)*scale, camera_pos + vec3_ignore_z(b)*scale)
    pg.draw.circle(surface_maneuver, (100, 100, 100), camera_pos + vec3_ignore_z(r[maneuver_index])*scale, 5)
        
def render_enviroment():
    surface_enviroment.fill("#3C3846")

    for body in bodies: # draw bodies
        for i in range(len(body.r)-1): # draw body main trajectory
            a = vec3_ignore_z(body.r[i])
            b = vec3_ignore_z(body.r[i+1])
            pg.draw.line(surface_enviroment, (255, 0, 255), camera_pos + a*scale, camera_pos + b*scale)
        pg.draw.circle(surface_enviroment, (0, 0, 100), camera_pos + vec3_ignore_z(body.r[maneuver_index])*scale, body.radius*scale)

    for i in range(len(r)-1): # draw vessel main trajectory
        a = r[i]
        b = r[i+1]
        pg.draw.line(surface_enviroment, (255, 0, 0), camera_pos + vec3_ignore_z(a)*scale, camera_pos + vec3_ignore_z(b)*scale)

def mouse_down_handler(pos):
    global maneuver_index

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
    render_maneuver()
    update_screen()

def key_down_handler(key):
    global scale, camera_pos

    if key == pg.K_KP_PLUS or key == pg.K_PLUS:
        scale *= 1 + delta_scale
        render_enviroment()
        render_maneuver()
        update_screen()
        return
    if key == pg.K_KP_MINUS or key == pg.K_MINUS:
        scale *= 1 - delta_scale
        render_enviroment()
        render_maneuver()
        update_screen()
        return
    if key == pg.K_UP:
        camera_pos.y += camera_speed
        render_enviroment()
        render_maneuver()
        update_screen()
        return
    if key == pg.K_DOWN:
        camera_pos.y -= camera_speed
        render_enviroment()
        render_maneuver()
        update_screen()
        return
    if key == pg.K_RIGHT:
        camera_pos.x -= camera_speed
        render_enviroment()
        render_maneuver()
        update_screen()
        return
    if key == pg.K_LEFT:
        camera_pos.x += camera_speed
        render_enviroment()
        render_maneuver()
        update_screen()
        return

def controller_event_handler(event, values):
    global vessel_step_size, vessel_sim_time, maneuver_sim_time

    steps = values.copy()

    for key, value in steps.items():
        try:
            steps[key] = int(value)
        except (ValueError, TypeError):
            steps[key] = 1

    # SIMULATION
    if event == "add_sim-step-size":
        vessel_step_size += steps["step_sim-step-size"]
        window_controller["display_sim-step-size"].update(vessel_step_size)
        return
    if event == "sub_sim-step-size":
        vessel_step_size -= steps["step_sim-step-size"]
        window_controller["display_sim-step-size"].update(vessel_step_size)
        return
    if event == "add_sim-time":
        vessel_sim_time += steps["step_sim-time"]
        window_controller["display_sim-time"].update(vessel_sim_time)
        return
    if event == "sub_sim-time":
        vessel_sim_time -= steps["step_sim-time"]
        window_controller["display_sim-time"].update(vessel_sim_time)
        return
    if event == "btn_sim-exec":
        global r, v
        r, v = calc_vessel(r0, v0, vessel_sim_time)
        render_enviroment()
        update_screen()
        return
    
    # BODY
    if event == "btn_body-sim-exec":
        calc_bodies()
        render_enviroment()
        update_screen()
        return

    # maneuver
    if event == "add_man-time":
        maneuver_sim_time += steps["step_man-time"]
        window_controller["display_man-time"].update(maneuver_sim_time)
        return
    if event == "sub_man-time":
        maneuver_sim_time -= steps["step_man-time"]
        window_controller["display_man-time"].update(maneuver_sim_time)
        return
    if event == "add_man-index":
        update_man_index(maneuver_index + steps["step_man-index"])
        return
    if event == "sub_man-index":
        update_man_index(maneuver_index - steps["step_man-index"])
        return
    
    # VEL
    if event == "add_man-vel-tg":
        maneuver_vel.x += steps["step_man-vel-tg"]
        window_controller["display_man-vel-tg"].update(maneuver_vel.x)
        return
    if event == "add_man-vel-norm":
        maneuver_vel.y += steps["step_man-vel-norm"]
        window_controller["display_man-vel-norm"].update(maneuver_vel.y)
        return
    if event == "add_man-vel-rad":
        maneuver_vel.z += steps["step_man-vel-rad"]
        window_controller["display_man-vel-rad"].update(maneuver_vel.z)
        return
    
    if event == "sub_man-vel-tg":
        maneuver_vel.x -= steps["step_man-vel-tg"]
        window_controller["display_man-vel-tg"].update(maneuver_vel.x)
        return
    if event == "sub_man-vel-norm":
        maneuver_vel.y -= steps["step_man-vel-norm"]
        window_controller["display_man-vel-norm"].update(maneuver_vel.y)
        return
    if event == "sub_man-vel-rad":
        maneuver_vel.z -= steps["step_man-vel-rad"]
        window_controller["display_man-vel-rad"].update(maneuver_vel.z)
        return
    
    # maneuver EXEC
    if event == "btn_man-sim-exec":
        global maneuver_v, maneuver_r
        print("maneuver RUNNING...")

        tg = maneuver_vel.x
        m_vel = v[maneuver_index].normalize() * tg

        maneuver_r, maneuver_v = calc_vessel(r[maneuver_index], v[maneuver_index] + m_vel, maneuver_sim_time)
        
        render_maneuver()
        update_screen()
        return

def update_man_index(index):
    global maneuver_index
    if index < 0 or index >= len(r) or index == maneuver_index: return
    maneuver_index = index
    window_controller["display_man-index"].update(index)
    render_maneuver()
    render_enviroment()
    update_screen()

bodies = []
with open("bodies_earth_ref.txt", "r") as file: # load bodies
    for line in file.readlines()[1:]:
        name, pos, vel, mass, radius = line.replace("\n", "").split("|")
        pos = Vector3(eval(pos))
        vel = Vector3(eval(vel))
        pos.z = 0 # ignore height
        vel.z = 0 # ignore height
        mass = float(mass)
        radius = float(radius)
        bodies.append(Body(name, pos, vel, mass, radius))
earth = get_body_by_name("Earth")
moon = get_body_by_name("Moon")

bodies = [earth, moon]

# RK4
vessel_step_size = 50
body_step_size = 1000

vessel_sim_time = 5000
maneuver_sim_time = 5000
body_sim_time = 5000000

# trajectory - vessel
r = []
v = []
r0 = earth.r[0] - Vector3(0, earth.radius+400000)
v0 = Vector3(7660, 0, 0)

# bodies orbit propagation
# bodies_comb = combinations(bodies, 2)

# PG
screen_size = Vector2(800, 800)      
screen = pg.display.set_mode(screen_size)
pg.display.set_caption("Orbit")

surface_enviroment = pg.Surface(screen_size)
surface_maneuver = pg.Surface(screen_size, pg.SRCALPHA)

delta_scale = 1e-1
scale = 15e-6

camera_pos = screen_size * 0.5
camera_speed = 100

maneuver_index = 0
maneuver_scale = 10
maneuver_vel = Vector3(0, 0, 0) # tg | norm | radial
maneuver_r = []
maneuver_v = []

# SG
font_sizes = [10, 12, 20, 30, 35]
font_by_size = lambda size: ("DS-Digital", size)
sg.theme("Dark")
sg.set_options(font=font_by_size(font_sizes[2]))
layout = [
    [sg.Text("==SIMULATION==", font=font_by_size(font_sizes[4]))],
    [sg.Text("Step Size"), sg.Text(str(vessel_step_size), key="display_sim-step-size", font=font_by_size(font_sizes[2])), sg.Button("+", key="add_sim-step-size"), sg.Button("-", key="sub_sim-step-size"), sg.InputText("1", size=(5, 1), key="step_sim-step-size")],
    [sg.Text("Time"), sg.Text(str(vessel_sim_time), key="display_sim-time", font=font_by_size(font_sizes[2])), sg.Button("+", key="add_sim-time"), sg.Button("-", key="sub_sim-time"), sg.InputText("1", size=(5, 1), key="step_sim-time")],
    [sg.Button("Simulate", key="btn_sim-exec", font=font_by_size(font_sizes[2]))],
    [sg.Text("==BODIES==", font=font_by_size(font_sizes[4]))],
    [sg.Button("Simulate", key="btn_body-sim-exec", font=font_by_size(font_sizes[2]))],
    [sg.Text("==MANEUVER==", font=font_by_size(font_sizes[4]))],
    [sg.Text("Index"), sg.Text(str(maneuver_index), key="display_man-index", font=font_by_size(font_sizes[2])), sg.Button("+", key="add_man-index"), sg.Button("-", key="sub_man-index"), sg.InputText("1", size=(5, 1), key="step_man-index")],
    [sg.Text("Time"), sg.Text(str(maneuver_sim_time), key="display_man-time", font=font_by_size(font_sizes[2])), sg.Button("+", key="add_man-time"), sg.Button("-", key="sub_man-time"), sg.InputText("1", size=(5, 1), key="step_man-time")],
    [sg.Text("--Vel--")],
    [sg.Text("tg"), sg.Text(str(maneuver_vel.x), key="display_man-vel-tg", font=font_by_size(font_sizes[2])), sg.Button("+", key="add_man-vel-tg"), sg.Button("-", key="sub_man-vel-tg"), sg.InputText("1", size=(5, 1), key="step_man-vel-tg")],
    [sg.Text("norm"), sg.Text(str(maneuver_vel.y), key="display_man-vel-norm", font=font_by_size(font_sizes[2])), sg.Button("+", key="add_man-vel-norm"), sg.Button("-", key="sub_man-vel-norm"), sg.InputText("1", size=(5, 1), key="step_man-vel-norm")],
    [sg.Text("rad"), sg.Text(str(maneuver_vel.z), key="display_man-vel-rad", font=font_by_size(font_sizes[2])), sg.Button("+", key="add_man-vel-rad"), sg.Button("-", key="sub_man-vel-rad"), sg.InputText("1", size=(5, 1), key="step_man-vel-rad")],
    [sg.Button("Execute maneuver", key="btn_man-sim-exec")],
]
window_controller = sg.Window("Controller", layout)

calc_bodies()
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