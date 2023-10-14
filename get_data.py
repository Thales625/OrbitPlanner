import krpc

conn = krpc.connect("Get Data", address="192.168.50.114", stream_port=None)
space_center = conn.space_center

bodies = space_center.bodies
earth = bodies["Earth"]

earth_ref = earth.reference_frame
earth_non_rot_ref = earth.non_rotating_reference_frame
earth_orb_ref = earth.orbital_reference_frame

header = "NAME|POSITION|VELOCITY|MASS|RADIUS\n"

txt_bodies_ref = [header]
txt_bodies_non_rot_ref = [header]
txt_bodies_orb_ref = [header]
for name, body in bodies.items():
    txt_bodies_ref.append(f"{name}|{body.position(earth_ref)}|{body.velocity(earth_ref)}|{body.mass}|{body.equatorial_radius}\n".replace(" ", ""))
    txt_bodies_non_rot_ref.append(f"{name}|{body.position(earth_non_rot_ref)}|{body.velocity(earth_non_rot_ref)}|{body.mass}|{body.equatorial_radius}\n".replace(" ", ""))
    txt_bodies_orb_ref.append(f"{name}|{body.position(earth_orb_ref)}|{body.velocity(earth_orb_ref)}|{body.mass}|{body.equatorial_radius}\n".replace(" ", ""))

conn.close()

with open("bodies_earth_ref.txt", "w") as file:
    file.writelines(txt_bodies_ref)

with open("bodies_earth_non_rot_ref.txt", "w") as file:
    file.writelines(txt_bodies_non_rot_ref)

with open("bodies_earth_orb_ref.txt", "w") as file:
    file.writelines(txt_bodies_orb_ref)