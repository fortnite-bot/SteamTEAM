import json

with open('C:\\Users\\hallo\\Downloads\\steam.json', 'r') as f:
    data = json.load(f)

median_playtimes = [game['median_playtime'] for game in data]

def calculate_median(numbers):
    sorted_numbers = sorted(numbers)
    n = len(sorted_numbers)
    
    if n % 2 == 0:
        return (sorted_numbers[n//2 - 1] + sorted_numbers[n//2]) / 2
    else:
        return sorted_numbers[n//2]
    



# Calculate median of medians
median_of_median_playtimes = calculate_median(median_playtimesa)

# Print result
print(f"De mediaan is: {median_of_median_playtimes}")
print(f"Het gemiddelde is: {int(sum(median_playtimes) / len(median_playtimes))}")
