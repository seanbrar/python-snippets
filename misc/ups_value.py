class UPS:
    def __init__(self, name, watts, va, price, runtime_half_load, runtime_full_load, joules):
        self.name = name
        self.watts = watts
        self.va = va
        self.price = price
        self.runtime_half_load = runtime_half_load
        self.runtime_full_load = runtime_full_load
        self.joules = joules

    def analyze_fit(self, required_watts):
        """
        Analyze how well this UPS fits the required load.
        Returns a dict with analysis results.
        """
        load_percentage = (required_watts / self.watts) * 100
        va_required = required_watts / 0.6  # Assuming typical 0.6 power factor for equipment
        
        # Check if unit is suitable for the load
        if load_percentage > 80:
            suitability = "OVERSIZED LOAD: Not recommended - too close to maximum capacity"
        elif load_percentage < 30:
            suitability = "OVERSIZED UPS: More capacity than needed - consider smaller unit"
        else:
            suitability = "GOOD FIT: Load is in optimal range"
            
        # Estimate realistic runtime using exponential decay
        # This gives more realistic estimates than linear interpolation
        load_ratio = required_watts / self.watts
        estimated_runtime = self.runtime_full_load * (1 / load_ratio) ** 1.5
        
        # Calculate cost efficiency only if it's a suitable fit
        if 30 <= load_percentage <= 80:
            value_ratio = (self.watts / self.price) * (1 - (load_percentage - 50) ** 2 / 10000)
        else:
            value_ratio = 0
            
        return {
            "suitability": suitability,
            "load_percentage": load_percentage,
            "estimated_runtime": estimated_runtime,
            "va_headroom": (self.va - va_required) / self.va * 100,
            "value_ratio": value_ratio,
            "price_per_watt": self.price / self.watts
        }

    def print_analysis(self, required_watts):
        """Print practical analysis for UPS selection."""
        analysis = self.analyze_fit(required_watts)
        
        print(f"\n=== {self.name} Analysis ===")
        print(f"Price: ${self.price}")
        print(f"Capacity: {self.watts}W / {self.va}VA")
        print(f"\nFor your {required_watts}W load:")
        print(f"Load Percentage: {analysis['load_percentage']:.1f}%")
        print(f"Estimated Runtime: {analysis['estimated_runtime']:.1f} minutes")
        print(f"VA Headroom: {analysis['va_headroom']:.1f}%")
        print(f"\nSUITABILITY: {analysis['suitability']}")
        print(f"Price per Watt: ${analysis['price_per_watt']:.2f}")
        if analysis['value_ratio'] > 0:
            print(f"Value Ratio: {analysis['value_ratio']:.2f}")
        print("-" * 50)

def compare_ups_units(required_watts):
    """Compare UPS units based on required load."""
    print(f"\nAnalyzing UPS options for {required_watts}W load requirement:")
    print("(Assuming typical 0.6 power factor for connected equipment)")
    print("=" * 50)
    
    # Create UPS objects
    apc = UPS("APC 1050VA", 
              watts=600,
              va=1050,
              price=145,
              runtime_half_load=10.6,
              runtime_full_load=2,
              joules=1103)
              
    cyberpower = UPS("CyberPower 1000VA",
                     watts=530,
                     va=1000,
                     price=130,
                     runtime_half_load=10,
                     runtime_full_load=2,
                     joules=1030)
    
    # Print analysis for each
    apc.print_analysis(required_watts)
    cyberpower.print_analysis(required_watts)
    
    # Provide a recommendation
    apc_analysis = apc.analyze_fit(required_watts)
    cyber_analysis = cyberpower.analyze_fit(required_watts)
    
    print("\nRECOMMENDATION:")
    if apc_analysis['value_ratio'] == 0 and cyber_analysis['value_ratio'] == 0:
        print("Neither unit is ideally sized for your needs.")
        if required_watts > min(apc.watts, cyberpower.watts) * 0.8:
            print("Consider a larger UPS unit.")
        else:
            print("Consider a smaller UPS unit.")
    else:
        better_unit = "APC" if apc_analysis['value_ratio'] > cyber_analysis['value_ratio'] else "CyberPower"
        if abs(apc_analysis['value_ratio'] - cyber_analysis['value_ratio']) < 0.1:
            print("Both units are similarly suitable - choose based on brand preference and price.")
        else:
            print(f"The {better_unit} unit is better suited for your needs.")

# Example usage:
compare_ups_units(450)  # Compare units for a 200W load