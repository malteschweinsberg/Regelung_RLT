import numpy as np


class PIController:
    def __init__(self, Kp, Ti, Td, min_output, max_output, deadband=0.0):
        self.Kp = Kp
        self.Ki = Kp / max(Ti, 1e-9)
        self.Kd = Kp * Td
        self.min = min_output
        self.max = max_output
        self.deadband = deadband
        self.integral = 0.0
        self.prev_error = 0.0
        self.last_output = (min_output + max_output) / 2

    def reset(self):
        self.integral = 0.0
        self.prev_error = 0.0

    def compute(self, setpoint, measured, dt):
        error = setpoint - measured
        if abs(error) <= self.deadband:
            return self.last_output

        p_term = self.Kp * error
        self.integral += error * dt
        i_term = self.Ki * self.integral
        d_term = self.Kd * (error - self.prev_error) / dt
        self.prev_error = error

        output = p_term + i_term + d_term
        if output > self.max:
            output = self.max
            self.integral -= (output - self.max) / self.Ki * 0.5
        elif output < self.min:
            output = self.min
            self.integral -= (output - self.min) / self.Ki * 0.5

        self.last_output = output
        return output
