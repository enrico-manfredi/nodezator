import random
import math

class CelestialBody:
    def __init__(self, name, body_type, mass, radius, semi_major_axis=None, eccentricity=None, orbital_period=None, temperature=None):
        self.name = name
        self.body_type = body_type  # "star", "planet", "moon", etc.
        self.mass = mass            # kg
        self.radius = radius        # m
        self.semi_major_axis = semi_major_axis  # m
        self.eccentricity = eccentricity
        self.orbital_period = orbital_period    # seconds
        self.temperature = temperature          # K

    def __repr__(self):
        return (f"<{self.body_type.capitalize()} {self.name}: "
                f"Mass={self.mass:.2e} kg, Radius={self.radius:.2e} m, "
                f"a={self.semi_major_axis}, e={self.eccentricity}>")

def generate_random_solar_system(system_name="RandomSystem"):
    # --- Constants ---
    G = 6.67430e-11  # gravitational constant
    M_earth = 5.972e24
    R_earth = 6.371e6
    M_sun = 1.989e30
    R_sun = 6.9634e8
    AU = 1.496e11

    # --- Generate Star ---
    star_mass = random.uniform(0.1, 2.0) * M_sun
    star_radius = R_sun * (star_mass / M_sun) ** 0.8  # rough mass-radius relation
    star_temp = random.uniform(3000, 8000)
    star = CelestialBody(
        name=f"{system_name}_Star",
        body_type="star",
        mass=star_mass,
        radius=star_radius,
        temperature=star_temp
    )

    # --- Generate Planets ---
    num_planets = random.randint(3, 10)
    planets = []
    for i in range(num_planets):
        a = random.uniform(0.3, 20) * AU
        e = random.uniform(0, 0.4)
        planet_mass = random.uniform(0.1, 300) * M_earth
        planet_radius = R_earth * (planet_mass / M_earth) ** (1/3)
        period = 2 * math.pi * math.sqrt(a**3 / (G * star_mass))
        temp = star_temp * math.sqrt(star_radius / (2 * a))  # blackbody approx

        planet = CelestialBody(
            name=f"{system_name}_Planet_{i+1}",
            body_type="planet",
            mass=planet_mass,
            radius=planet_radius,
            semi_major_axis=a,
            eccentricity=e,
            orbital_period=period,
            temperature=temp
        )
        planets.append(planet)

    # --- Combine ---
    system_bodies = [star] + planets
    return system_bodies

main_callable = generate_random_solar_system

# Example usage:
if __name__ == "__main__":
    system = generate_random_solar_system("Andara")
    for body in system:
        print(body)
