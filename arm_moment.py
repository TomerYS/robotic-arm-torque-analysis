import math
import tkinter as tk
from tkinter import ttk
import csv
import os

class DualScenarioApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Robotic Arm - Torque Analysis")
        self.geometry("1250x700")

        # -------------------------------------------------------
        # 1) Define parameters (only masses, no link lengths) and motor limits
        # -------------------------------------------------------
        self.PARAMS = [
            {"name": "Rock Mass [kg]",      "default": 4.0,   "min": 0,   "max": 10,  "key": "rock_mass"},
            {"name": "Link 1 Mass [kg]",    "default": 0.367,   "min": 0,   "max": 10,  "key": "m1"},
            {"name": "Link 2 Mass [kg]",    "default": 0.44,   "min": 0,   "max": 10,  "key": "m2"},
            {"name": "Link 3 Mass [kg]",    "default": 0.15,   "min": 0,   "max": 10,  "key": "m3"},
            {"name": "Joint elbow Mass [kg]",   "default": 1.09, "min": 0, "max": 10,  "key": "m4"},
            {"name": "Joint wrist Mass [kg]",   "default": 0.82, "min": 0, "max": 10,  "key": "m5"},
        ]
        self.MOTOR_LIMITS = [
            {"name": "Shoulder Limit [Nm]", "default": 33.0,  "min": 0,   "max": 200, "key": "shoulder_limit"},
            {"name": "Elbow Limit [Nm]",    "default": 21.0,   "min": 0,   "max": 100, "key": "elbow_limit"},
        ]
        self.L1_mm = 400
        self.L2_mm = 450
        self.L3_mm = 180
        self.param_vars = {}
        self.limit_vars = {}
        self.row_index = 0
        self.build_ui()
        self.update_scenarios()
    # -------------------------------------------------------------------------
    # BUILD THE GUI
    # -------------------------------------------------------------------------
    def build_ui(self):
        for p in self.PARAMS:
            lbl = ttk.Label(self, text=p["name"])
            lbl.grid(row=self.row_index, column=0, sticky="w", padx=5, pady=1)
            var = tk.DoubleVar(value=p["default"])
            var.trace_add("write", self.on_var_changed)
            self.param_vars[p["key"]] = var
            scale = ttk.Scale(
                self, from_=p["min"], to_=p["max"],
                variable=var, orient=tk.HORIZONTAL, length=200
            )
            scale.grid(row=self.row_index, column=1, padx=5, pady=1)
            ent = ttk.Entry(self, textvariable=var, width=8)
            ent.grid(row=self.row_index, column=2, padx=5, pady=1)
            self.row_index += 1
        for p in self.MOTOR_LIMITS:
            lbl = ttk.Label(self, text=p["name"])
            lbl.grid(row=self.row_index, column=0, sticky="w", padx=5, pady=1)
            var = tk.DoubleVar(value=p["default"])
            var.trace_add("write", self.on_var_changed)
            self.limit_vars[p["key"]] = var
            scale = ttk.Scale(
                self, from_=p["min"], to_=p["max"],
                variable=var, orient=tk.HORIZONTAL, length=200
            )
            scale.grid(row=self.row_index, column=1, padx=5, pady=1)
            ent = ttk.Entry(self, textvariable=var, width=8)
            ent.grid(row=self.row_index, column=2, padx=5, pady=1)
            self.row_index += 1
        self.scenario1_label = ttk.Label(self, text="Scenario 1", font=("Arial", 10, "bold"))
        self.scenario1_label.grid(row=self.row_index, column=0, columnspan=3, sticky="w", pady=1)
        self.row_index += 1
        self.scenario2_label = ttk.Label(self, text="Scenario 2", font=("Arial", 10, "bold"))
        self.scenario2_label.grid(row=self.row_index, column=0, columnspan=3, sticky="w", pady=1)
        self.row_index += 1
        frame = ttk.Frame(self)
        frame.grid(row=self.row_index, column=0, columnspan=3, pady=1)
        self.canvas1 = tk.Canvas(frame, width=550, height=400, bg="white")
        self.canvas1.pack(side=tk.LEFT, padx=5)
        self.canvas2 = tk.Canvas(frame, width=550, height=400, bg="white")
        self.canvas2.pack(side=tk.LEFT, padx=5)
        self.row_index += 1

        save_button = ttk.Button(self, text="Save to CSV", command=self.save_to_csv)
        save_button.grid(row=self.row_index, column=0, columnspan=3, pady=1)
        self.row_index += 1
    # -------------------------
    # 
    # 
    def save_to_csv(self):
        """Save the current parameter and limit values to a CSV file."""
        # Define the file name
        file_name = "robotic_arm_data.csv"

        # Collect the current values
        data = {
            **{key: var.get() for key, var in self.param_vars.items()},
            **{key: var.get() for key, var in self.limit_vars.items()}
        }

        # Check if the file exists to determine if we need a header
        file_exists = os.path.isfile(file_name)

        # Write the data to the CSV file
        with open(file_name, mode="a", newline="") as file:
            writer = csv.writer(file)

            # Write the header if the file is new
            if not file_exists:
                writer.writerow(data.keys())

            # Write the data row
            writer.writerow(data.values())

        # Notify the user
        print(f"Data saved to {file_name}")

    # ------------------------------------------------
    # EVENT: a parameter changed
    # -------------------------------------------------------------------------
    def on_var_changed(self, *args):
        self.update_scenarios()
    # -------------------------------------------------------------------------
    # UPDATE SCENARIOS
    # -------------------------------------------------------------------------
    def update_scenarios(self):
        """
        - Scenario 1: Hard-coded geometry -> compute & display Shoulder/Elbow torque
        - Scenario 2: Use the (fixed) link lengths but vary angles to find max X
        """
        try:
            rock_mass = self.param_vars["rock_mass"].get()
            m1 = self.param_vars["m1"].get()
            m2 = self.param_vars["m2"].get()
            m3 = self.param_vars["m3"].get()
            m4 = self.param_vars["m4"].get()
            m5 = self.param_vars["m5"].get()
            shoulder_limit = self.limit_vars["shoulder_limit"].get()
            elbow_limit    = self.limit_vars["elbow_limit"].get()
            Ts1, Te1 = self.calculate_scenario1_torques(m1, m2, m3, m4, m5, rock_mass)
            Ts1_abs = abs(Ts1)
            Te1_abs = abs(Te1)
            self.scenario1_label.config(
                text=(
                    f"Scenario 1: "
                    f"Shoulder Torque = {Ts1_abs:.3f} Nm   |   "
                    f"Elbow Torque = {Te1_abs:.3f} Nm"
                )
            )
            self.draw_scenario_fixed_points(self.canvas1, label="Scenario 1")
            L1_m = self.L1_mm / 1000.0
            L2_m = self.L2_mm / 1000.0
            L3_m = self.L3_mm / 1000.0
            max_x, best_t1, best_t2, best_t3 = self.find_max_X(
                L1_m, L2_m, L3_m,
                m1, m2, m3, m4, m5,
                rock_mass,
                shoulder_limit, elbow_limit
            )
            self.scenario2_label.config(
                text=(f"Scenario 2 (Max X): "
                      f"X = {max_x*1000:.1f} mm   |   "
                      f"Angles = ({abs(math.degrees(best_t1)):.1f}°, "
                                 f"{abs(math.degrees(best_t2)):.1f}°)")
            )
            self.draw_scenario(
                self.canvas2,
                best_t1, best_t2, best_t3,
                self.L1_mm, self.L2_mm, self.L3_mm,
                label="Scenario 2",
                highlight_distance=max_x*1000
            )
        except ValueError:
            self.scenario1_label.config(text="Invalid Input", foreground="red")
            self.scenario2_label.config(text="Invalid Input", foreground="red")
    # -------------------------------------------------------------------------
    # SCENARIO 1: DIRECT TORQUE COMPUTATION
    # -------------------------------------------------------------------------
    def calculate_scenario1_torques(self, m1, m2, m3, m4, m5, rock_mass):
        """
        Return (ShoulderTorque, ElbowTorque) for the
        following geometry (in cm):

             O=(0,30) -- A=... -- B=(40,18) -- E=(40,0)

        We'll treat:
         - Link1 mass at midpoint of O->A
         - Link2 mass at midpoint of A->B
         - Link3 mass at midpoint of B->E
         - Elbow-joint mass at A
         - Wrist-joint mass at B
         - Rock at E

        Then:
         - Shoulder pivot = O
         - Elbow pivot = A
        """
        g = 9.87
        Ox, Oy = (0.0, 30.0)
        Ax, Ay = (
            (6595.0 / 436.0) + (27.0  * math.sqrt(116319.0) / 872.0),
            (22203.0 / 872.0) + (45.0 * math.sqrt(116319.0) / 436.0)
        )
        Bx, By = (40.0, 18.0)
        Ex, Ey = (40.0,  0.0)
        def cm_to_m(c): return 0.01 * c
        O_m = (cm_to_m(Ox), cm_to_m(Oy))
        A_m = (cm_to_m(Ax), cm_to_m(Ay))
        B_m = (cm_to_m(Bx), cm_to_m(By))
        E_m = (cm_to_m(Ex), cm_to_m(Ey))
        link1_mid = ((O_m[0] + A_m[0]) / 2.0, (O_m[1] + A_m[1]) / 2.0)
        link2_mid = ((A_m[0] + B_m[0]) / 2.0, (A_m[1] + B_m[1]) / 2.0)
        link3_mid = ((B_m[0] + E_m[0]) / 2.0, (B_m[1] + E_m[1]) / 2.0)
        elbow_pos = A_m
        wrist_pos = B_m
        rock_pos = E_m
        T_shoulder = 0.0
        for (mx, my, mass) in [
            (link1_mid[0], link1_mid[1], m1),
            (link2_mid[0], link2_mid[1], m2),
            (link3_mid[0], link3_mid[1], m3),
            (elbow_pos[0], elbow_pos[1], m4),
            (wrist_pos[0], wrist_pos[1], m5),
            (rock_pos[0],  rock_pos[1],  rock_mass),
        ]:
            rx = mx - O_m[0]
            ry = my - O_m[1]
            Fx = 0.0
            Fy = -mass * g
            torque_i = rx * Fy - ry * Fx
            T_shoulder += torque_i
        T_elbow = 0.0
        for (mx, my, mass) in [
            (link2_mid[0], link2_mid[1], m2),
            (link3_mid[0], link3_mid[1], m3),
            (wrist_pos[0], wrist_pos[1], m5),
            (rock_pos[0],  rock_pos[1],  rock_mass),
        ]:
            rx = mx - A_m[0]
            ry = my - A_m[1]
            Fx = 0.0
            Fy = -mass * g
            torque_i = rx * Fy - ry * Fx
            T_elbow += torque_i
        return (T_shoulder, T_elbow)

    # -------------------------------------------------------------------------
    # SCENARIO 2: FIND MAX X
    # -------------------------------------------------------------------------
    def find_max_X(self, L1_m, L2_m, L3_m,
                   m1, m2, m3, m4, m5, rock_mass,
                   shoulder_limit, elbow_limit):
        """
        Brute-force search for angles that produce the largest end-effector X
        subject to:
          - B (the end of link2) is at y=0.18 m
          - Link3 is straight down => theta3 = -90°
          - E is then at y=0
          - The joint torques must not exceed (shoulder_limit, elbow_limit).
        """
        max_x = 0.0
        best_t1 = 0.0
        best_t2 = 0.0
        best_t3 = 0.0
        t3 = math.radians(90)
        for t1_deg in range(-90,30):
            for t2_deg in range(0, 271):
                t1 = math.radians(t1_deg)
                t2 = math.radians(t2_deg)
                yB = L1_m * math.sin(t1) + L2_m * math.sin(t1 + t2)
                if abs(yB - 0.12) < 0.001:
                    Ts, Te = self.calculate_torques(
                        t1, t2, t3,
                        L1_m, L2_m, L3_m,
                        m1, m2, m3,
                        m4, m5,
                        rock_mass
                    )
                    if (abs(Ts) <= shoulder_limit) and (abs(Te) <= elbow_limit):
                        x_end = (
                            L1_m * math.cos(t1)
                            + L2_m * math.cos(t1 + t2)
                            + L3_m * math.cos(t3)
                        )
                        if x_end > max_x:
                            max_x = x_end
                            best_t1 = t1
                            best_t2 = t2
                            best_t3 = t3
        return max_x, best_t1, best_t2, best_t3

    # -------------------------------------------------------------------------
    # TORQUE CALCULATION (for scenario2)
    # -------------------------------------------------------------------------
    def calculate_torques(self, theta1, theta2, theta3,
                        L1_m, L2_m, L3_m,
                        m1, m2, m3, m4, m5, rock_mass):
        """
        Approx torque at shoulder (Ts) & elbow (Te), 
        now including the elbow mass (m4) at the elbow pivot
        and the wrist mass (m5) at the wrist pivot,
        plus the rock at the end.

        Pivot layout in scenario2 (standard 2D):
        - Shoulder pivot at (0,0)
        - Elbow pivot at (Xel, Yel) = end of link1
        - Wrist pivot at (Xwr, Ywr) = end of link2
        """
        g = 9.87

        x1 = (L1_m/2) * math.cos(theta1)
        y1 = (L1_m/2) * math.sin(theta1)
        F1 = m1*g
        x2 = (L1_m * math.cos(theta1) +
            (L2_m/2)*math.cos(theta1 + theta2))
        y2 = (L1_m * math.sin(theta1) +
            (L2_m/2)*math.sin(theta1 + theta2))
        F2 = m2*g
        x3 = (L1_m * math.cos(theta1) +
            L2_m * math.cos(theta1 + theta2) +
            (L3_m/2)*math.cos(theta3))
        y3 = (L1_m * math.sin(theta1) +
            L2_m * math.sin(theta1 + theta2) +
            (L3_m/2)*math.sin(theta3))
        F3 = m3*g

        # ---------------------------
        # Joint masses
        # ---------------------------
        x_elbow = L1_m * math.cos(theta1)
        y_elbow = L1_m * math.sin(theta1)
        F4 = m4*g
        x_wrist = (L1_m * math.cos(theta1) +
                L2_m * math.cos(theta1 + theta2))
        y_wrist = (L1_m * math.sin(theta1) +
                L2_m * math.sin(theta1 + theta2))
        F5 = m5*g
        # ---------------------------
        # Rock at end
        # ---------------------------
        xr = (L1_m * math.cos(theta1) +
            L2_m * math.cos(theta1 + theta2) +
            L3_m * math.cos(theta3))
        yr = (L1_m * math.sin(theta1) +
            L2_m * math.sin(theta1 + theta2) +
            L3_m * math.sin(theta3))
        Fr = rock_mass*g
        def torque_shoulder(x, y, mass_g):
            return x * (-mass_g)
        Ts = 0.0
        Ts += torque_shoulder(x1, y1, F1)
        Ts += torque_shoulder(x2, y2, F2)
        Ts += torque_shoulder(x3, y3, F3)
        Ts += torque_shoulder(x_elbow, y_elbow, F4)
        Ts += torque_shoulder(x_wrist, y_wrist, F5)
        Ts += torque_shoulder(xr, yr, Fr)

        # ---------------------------
        # Elbow torque (about end of link1 = (x_elbow, y_elbow))
        # We only sum link2, link3, wrist, rock masses (and possibly elbow mass 
        # if it's not exactly at the pivot, but we assume it is).
        # ---------------------------
        def torque_elbow(x, y, pivot_x, pivot_y, mass_g):
            rx = x - pivot_x
            ry = y - pivot_y
            return rx * (-mass_g)

        Te = 0.0
        # link2 midpoint
        Te += torque_elbow(x2, y2, x_elbow, y_elbow, F2)
        # link3 midpoint
        Te += torque_elbow(x3, y3, x_elbow, y_elbow, F3)
        # wrist mass
        Te += torque_elbow(x_wrist, y_wrist, x_elbow, y_elbow, F5)
        # rock
        Te += torque_elbow(xr, yr, x_elbow, y_elbow, Fr)

        return Ts, Te

    # -------------------------------------------------------------------------
    # DRAW SCENARIO 1: FIXED FOUR POINTS
    # -------------------------------------------------------------------------
    def draw_scenario_fixed_points(self, canvas, label=""):
        """
        Hard-code the 4 points in cm:
           Origin = (0, 30)
           A = ...
           B = (40, 18)
           End = (40, 0)
        """
        canvas.delete("all")
        self.draw_grid_and_axes(canvas, 550, 400, 0, 400, spacing=50)
        canvas.create_text(10, 10, text=label, anchor="nw", font=("Arial",12,"bold"))
        Ox, Oy = (0.0, 30.0)
        Ax = (6595.0/436.0) + (27.0  * math.sqrt(116319.0) / 872.0)
        Ay = (22203.0/872.0) + (45.0 * math.sqrt(116319.0) / 436.0)
        Bx, By = (40.0, 18.0)
        Ex, Ey = (40.0,  0.0)
        scale = 6.0
        offset_x = 60
        offset_y = 350
        def to_canvas(x_cm, y_cm):
            cx = offset_x + x_cm * scale
            cy = offset_y - y_cm * scale
            return (cx, cy)
        Opx, Opy = to_canvas(Ox, Oy)
        Apx, Apy = to_canvas(Ax, Ay)
        Bpx, Bpy = to_canvas(Bx, By)
        Epx, Epy = to_canvas(Ex, Ey)
        canvas.create_line(Opx, Opy, Apx, Apy, width=4, fill="blue")
        canvas.create_line(Apx, Apy, Bpx, Bpy, width=4, fill="green")
        canvas.create_line(Bpx, Bpy, Epx, Epy, width=4, fill="red")
        for (xx, yy) in [(Opx, Opy), (Apx, Apy), (Bpx, Bpy), (Epx, Epy)]:
            r = 4
            canvas.create_oval(xx-r, yy-r, xx+r, yy+r, fill="black")
        canvas.create_text(Opx+10, Opy, text="Origin", anchor="w", fill="blue")
        canvas.create_text(Apx+10, Apy, text="A",      anchor="w", fill="blue")
        canvas.create_text(Bpx+10, Bpy, text="B",      anchor="w", fill="blue")
        canvas.create_text(Epx+10, Epy, text="End",    anchor="w", fill="blue")

    # -------------------------------------------------------------------------
    # DRAW SCENARIO 2
    # -------------------------------------------------------------------------
    def to_real_mm(canvas_x, canvas_y, base_x, base_y, px_per_m=200):
        """
        Return (real_x_mm, real_y_mm) in standard 'math up is positive' coords,
        assuming the base pivot is at (base_x, base_y) on the canvas.
        """
        real_x_m = (canvas_x - base_x) / px_per_m
        real_y_m = (base_y - canvas_y) / px_per_m
        return (real_x_m*1000, real_y_m*1000)

    def draw_scenario(self, canvas, t1, t2, t3,
                      L1_mm, L2_mm, L3_mm,
                      label="", highlight_distance=None):
        """
        Draw an arm with angles (t1,t2,t3) using the fixed link lengths.
        """
        canvas.delete("all")
        self.draw_grid_and_axes(canvas, 550, 400, 300, 300, spacing=50)

        canvas.create_text(10, 10, text=label, anchor="nw", font=("Arial",12,"bold"))

        scale = 200
        bx, by = 300, 300

        L1_m = L1_mm/1000.0
        L2_m = L2_mm/1000.0
        L3_m = L3_mm/1000.0

        # Link1 end
        x1 = bx + scale * L1_m * math.cos(t1)
        y1 = by + scale * L1_m * math.sin(t1)
        # Link2 end
        x2 = x1 + scale * L2_m * math.cos(t1 + t2)
        y2 = y1 + scale * L2_m * math.sin(t1 + t2)
        # Link3 end
        x3 = x2 + scale * L3_m * math.cos(t3)
        y3 = y2 + scale * L3_m * math.sin(t3)

        # Draw links
        canvas.create_line(bx, by, x1, y1, width=4, fill="blue")
        canvas.create_line(x1, y1, x2, y2, width=4, fill="green")
        canvas.create_line(x2, y2, x3, y3, width=4, fill="red")

        # Draw joints
        r = 5
        points = [
            ("O",   (bx,  by)),
            ("A", (x1, y1)),
            ("B", (x2, y2)),
            ("E",    (x3, y3)),
        ]
        for name, (xx, yy) in points:
            canvas.create_oval(xx-r, yy-r, xx+r, yy+r, fill="black")
            rx_mm = -((300 - xx) / 200)*1000
 
            ry_mm = -((yy - 300) / 200)*1000+300

            coords_label = f"{name}\n({rx_mm:.1f}mm, {ry_mm:.1f}mm)"
            canvas.create_text(xx+10, yy-50, text=coords_label, anchor="w", fill="blue", font=("Arial",8))
        shoulder_deg = math.degrees(t1)
        elbow_deg    = math.degrees(t2)
        angle_text = f"Shoulder={abs(shoulder_deg):.1f}°, Elbow={abs(elbow_deg):.1f}°"
        canvas.create_text(bx+80, by-250, text=angle_text, fill="blue", anchor="w")

        if highlight_distance is not None:
            canvas.create_text(10, 30,
                               text=f"Distance = {highlight_distance:.1f} mm",
                               anchor="nw", fill="maroon")

    # -------------------------------------------------------------------------
    # DRAW GRID + AXES
    # -------------------------------------------------------------------------
    def draw_grid_and_axes(self, canvas, width, height, origin_x, origin_y, spacing=50):
        """Draw a simple grid of lines, plus thick X/Y axes at (origin_x,origin_y)."""
        # Grid lines
        for vx in range(0, width, spacing):
            canvas.create_line(vx, 0, vx, height, fill="#e0e0e0")
        for hy in range(0, height, spacing):
            canvas.create_line(0, hy, width, hy, fill="#e0e0e0")

        # Axes
        canvas.create_line(0, origin_y, width, origin_y, width=2, fill="black")
        canvas.create_line(origin_x, 0, origin_x, height, width=2, fill="black")

        # Axis labels
        canvas.create_text(width-10, origin_y-10, text="X", fill="black")
        canvas.create_text(origin_x+20, 10,        text="Y", fill="black")


# -------------------------------------------------------------------------
# RUN THE APP
# -------------------------------------------------------------------------
if __name__ == "__main__":
    app = DualScenarioApp()
    app.mainloop()
