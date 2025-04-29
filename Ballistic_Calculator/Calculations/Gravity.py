import numpy as np

def gravityAcceleration(latitude=55.75, altitude=200):
    phi = np.radians(latitude)
    g = 9.780318 * (1 + 0.0053024 * np.sin(phi)**2 - 0.0000058 * np.sin(2 * phi)**2) - 0.000003085 * altitude
    return g
