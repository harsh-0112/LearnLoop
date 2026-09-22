"""Hand-authored concept graphs used by the synthetic data generator.

Each entry is ``(name, difficulty_level, description, [prerequisite names])`` and the
lists are ordered so that every prerequisite appears before the concept using it.
"""

ConceptSpec = tuple[str, int, str, list[str]]

ALGEBRA: list[ConceptSpec] = [
    ("Integer Operations", 1, "Adding, subtracting, multiplying and dividing integers.", []),
    ("Order of Operations", 1, "Evaluating expressions using PEMDAS.", ["Integer Operations"]),
    ("Fractions and Decimals", 1, "Equivalence and arithmetic with rational numbers.", ["Integer Operations"]),
    ("Ratios and Proportions", 2, "Comparing quantities and solving proportions.", ["Fractions and Decimals"]),
    ("Percentages", 2, "Percent increase, decrease and conversions.", ["Ratios and Proportions"]),
    ("Exponents", 2, "Integer exponents and the laws of exponents.", ["Integer Operations"]),
    ("Radicals", 3, "Square roots, simplification and rational exponents.", ["Exponents"]),
    ("Variables and Expressions", 1, "Translating situations into algebraic expressions.", ["Order of Operations"]),
    ("Combining Like Terms", 2, "Simplifying expressions by grouping like terms.", ["Variables and Expressions"]),
    ("Distributive Property", 2, "Expanding products over sums.", ["Combining Like Terms"]),
    ("Linear Equations One Variable", 2, "Solving ax + b = c and multi-step equations.", ["Distributive Property"]),
    ("Linear Inequalities", 3, "Solving and graphing inequalities in one variable.", ["Linear Equations One Variable"]),
    ("Absolute Value Equations", 3, "Equations and inequalities involving absolute value.", ["Linear Inequalities"]),
    ("Coordinate Plane", 1, "Plotting points and reading graphs.", ["Integer Operations"]),
    ("Slope of a Line", 2, "Rate of change between two points.", ["Coordinate Plane", "Fractions and Decimals"]),
    ("Graphing Linear Functions", 3, "Slope-intercept and point-slope forms.", ["Slope of a Line", "Linear Equations One Variable"]),
    ("Systems of Linear Equations", 3, "Substitution and elimination methods.", ["Graphing Linear Functions"]),
    ("Function Notation", 2, "Domain, range and evaluating f(x).", ["Variables and Expressions"]),
    ("Polynomial Arithmetic", 3, "Adding, subtracting and multiplying polynomials.", ["Distributive Property", "Exponents"]),
    ("Factoring Quadratics", 4, "Factoring trinomials and differences of squares.", ["Polynomial Arithmetic"]),
    ("Quadratic Equations", 4, "Solving by factoring, completing the square and the formula.", ["Factoring Quadratics", "Radicals"]),
    ("Quadratic Graphs", 4, "Parabolas, vertex form and transformations.", ["Quadratic Equations", "Graphing Linear Functions"]),
    ("Rational Expressions", 4, "Simplifying and operating on algebraic fractions.", ["Factoring Quadratics", "Fractions and Decimals"]),
    ("Exponential Functions", 5, "Growth, decay and exponential graphs.", ["Exponents", "Function Notation"]),
    ("Logarithms", 5, "Logarithmic notation, laws and equations.", ["Exponential Functions"]),
]

PHYSICS: list[ConceptSpec] = [
    ("Units and Measurement", 1, "SI units, conversions and significant figures.", []),
    ("Vectors and Scalars", 2, "Vector components, addition and resolution.", ["Units and Measurement"]),
    ("Displacement and Velocity", 2, "Position, displacement and average velocity.", ["Vectors and Scalars"]),
    ("Acceleration", 2, "Rate of change of velocity and motion graphs.", ["Displacement and Velocity"]),
    ("Kinematic Equations", 3, "Constant-acceleration equations of motion.", ["Acceleration"]),
    ("Projectile Motion", 4, "Two-dimensional motion under gravity.", ["Kinematic Equations", "Vectors and Scalars"]),
    ("Newtons First Law", 2, "Inertia and equilibrium of forces.", ["Vectors and Scalars"]),
    ("Newtons Second Law", 3, "F = ma and free-body diagrams.", ["Newtons First Law", "Acceleration"]),
    ("Newtons Third Law", 3, "Action-reaction pairs and interaction forces.", ["Newtons Second Law"]),
    ("Friction", 3, "Static and kinetic friction on surfaces.", ["Newtons Second Law"]),
    ("Circular Motion", 4, "Centripetal acceleration and force.", ["Newtons Second Law", "Kinematic Equations"]),
    ("Work and Energy", 3, "Work done by forces and the work-energy theorem.", ["Newtons Second Law"]),
    ("Kinetic and Potential Energy", 3, "Mechanical energy and energy transfer.", ["Work and Energy"]),
    ("Conservation of Energy", 4, "Energy conservation in isolated systems.", ["Kinetic and Potential Energy"]),
    ("Power", 3, "Rate of energy transfer.", ["Work and Energy"]),
    ("Momentum and Impulse", 4, "Linear momentum and impulse-momentum theorem.", ["Newtons Second Law"]),
    ("Collisions", 4, "Elastic and inelastic collisions.", ["Momentum and Impulse", "Conservation of Energy"]),
    ("Torque", 4, "Rotational effect of forces about a pivot.", ["Newtons Second Law", "Vectors and Scalars"]),
    ("Rotational Motion", 5, "Angular kinematics and moment of inertia.", ["Torque", "Circular Motion"]),
    ("Gravitation", 4, "Newton's law of universal gravitation and orbits.", ["Circular Motion"]),
    ("Simple Harmonic Motion", 5, "Springs, pendulums and oscillation equations.", ["Conservation of Energy", "Circular Motion"]),
    ("Waves", 4, "Wavelength, frequency and wave speed.", ["Simple Harmonic Motion"]),
    ("Sound", 4, "Sound waves, intensity and the Doppler effect.", ["Waves"]),
    ("Electrostatics", 4, "Charge, Coulomb's law and electric fields.", ["Vectors and Scalars"]),
    ("Electric Circuits", 5, "Current, resistance, Ohm's law and simple circuits.", ["Electrostatics", "Power"]),
]

CURRICULUM: dict[str, list[ConceptSpec]] = {
    "Algebra": ALGEBRA,
    "Physics": PHYSICS,
}
