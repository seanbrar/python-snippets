def calculate_ac_value():
    C = float(input("Enter the cost of the unit (including installation): "))
    S = float(input("Enter the SEER rating of the new unit: "))
    O = float(input("Enter the estimated years of ownership: "))
    U = 38  # Estimated daily usage in kWh by the AC system
    E = 0.2233  # Estimated average electricity cost per kWh | Cost of electricity over a period divided by kWh over that same period

    ES = 1 - (16 / S) # Energy Savings compared to SEER 16 as a percentage
    A = ((U * E * ES) * 365) # Annual savings
    ROI = ((A * O) - C) / C * 100 # Return on Investment over ownership period
    V = A / C # Annual savings per initial dollar spent

    print(f"\nEnergy savings compared to SEER 16: {ES:.2%}")
    print(f"Annual savings: ${A:.2f}")
    print(f"ROI over ownership period: {ROI:.2f}%")
    print(f"Annual Savings per Dollar Spent: ${V:.4f}")

if __name__ == "__main__":
    calculate_ac_value()
