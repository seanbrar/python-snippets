# Default values. Change these to match your area.
DEFAULT_DAILY_USAGE_KWH = 38
DEFAULT_ELECTRICITY_COST = 0.2233

def get_positive_float(prompt, default=None):
    """
    Prompts the user for a positive float value.
    If a default value is provided, it will be used if the user enters nothing.
    """
    while True:
        try:
            user_input = input(prompt)
            if user_input == "" and default is not None:
                return default
            value = float(user_input)
            if value < 0:
                print("Please enter a positive number.")
            else:
                return value
        except ValueError:
            print("Invalid input. Please enter a numeric value.")

def calculate_energy_savings(S):
    """Calculates energy savings compared to SEER 16."""
    return max(1 - (16 / S), 0)

def calculate_annual_savings(U, E, ES):
    """Calculates annual savings based on usage, electricity cost, and energy savings."""
    return (U * E * ES) * 365

def calculate_roi(A, O, C):
    """Calculates Return on Investment over the ownership period."""
    return ((A * O) - C) / C * 100

def calculate_annual_savings_per_dollar(A, C):
    """Calculates annual savings per dollar spent."""
    return A / C

def calculate_ac_value():
    """
    Calculates and prints the energy savings, annual savings, ROI, and annual savings per dollar
    spent for an AC unit based on user inputs.
    """
    print("\n--- AC Value Calculator ---")
    C = get_positive_float("Enter the cost of the unit (including installation): $")
    S = get_positive_float("Enter the SEER/SEER2 rating of the new unit: ")
    if S < 16:
        print("Warning: SEER rating below 16 may result in negative energy savings compared to SEER 16.")
    O = get_positive_float("Enter the estimated years of ownership: ")
    U = get_positive_float(f"Enter the estimated daily usage in kWh by the AC system (default {DEFAULT_DAILY_USAGE_KWH}): ", DEFAULT_DAILY_USAGE_KWH)
    E = get_positive_float(f"Enter the average electricity cost per kWh (default ${DEFAULT_ELECTRICITY_COST:.4f}): ", DEFAULT_ELECTRICITY_COST)

    ES = calculate_energy_savings(S)
    A = calculate_annual_savings(U, E, ES)
    ROI = calculate_roi(A, O, C)
    V = calculate_annual_savings_per_dollar(A, C)

    print("\n--- AC Value Analysis ---")
    print(f"Energy Savings compared to SEER 16: {ES:.2%}")
    print(f"Annual Savings: ${A:,.2f}")
    print(f"Return on Investment over {O} years: {ROI:.2f}%")
    print(f"Annual Savings per Dollar Spent: ${V:.4f}")
    print("--------------------------\n")

def main():
    """Main function to run the AC Value Calculator."""
    print("Welcome to the AC Value Calculator!")
    while True:
        calculate_ac_value()
        cont = input("Would you like to perform another calculation? (y/n): ").strip().lower()
        if cont != 'y':
            print("Thank you for using the AC Value Calculator!")
            break

if __name__ == "__main__":
    main()
