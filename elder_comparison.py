name1 = input("Enter first name: ")
age1 = int(input(f"Enter {name1}'s age: "))

name2 = input("Enter second name: ")
age2 = int(input(f"Enter {name2}'s age: "))

if age1 > age2:
    print(f"{name1} is elder than {name2}")
elif age2 > age1:
    print(f"{name2} is elder than {name1}")
else:
    print(f"{name1} and {name2} are of the same age")
