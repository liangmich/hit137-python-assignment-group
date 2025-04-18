import turtle

def draw_branch(t, branch_length, angle_left, angle_right, depth, reduction_factor, max_depth):
    if depth == 0 or branch_length < 1:
        return

    # Change color based on depth
    if depth == max_depth:
        t.color("brown")
        t.pensize(5)
    else:
        t.color("green")
        t.pensize(2)

    # Draw the branch
    t.forward(branch_length)

    # Left branch
    t.left(angle_left)
    draw_branch(t, branch_length * reduction_factor, angle_left, angle_right, depth - 1, reduction_factor, max_depth)

    # Go to the other side
    t.right(angle_left + angle_right)
    draw_branch(t, branch_length * reduction_factor, angle_left, angle_right, depth - 1, reduction_factor, max_depth)

    # Go back to original position and direction
    t.left(angle_right)
    t.backward(branch_length)

def main():
    # Get user input
    angle_left = float(input("Enter left branch angle (degrees): "))
    angle_right = float(input("Enter right branch angle (degrees): "))
    start_length = float(input("Enter starting branch length (pixels): "))
    depth = int(input("Enter recursion depth: "))
    reduction_factor = float(input("Enter branch length reduction factor (e.g., 0.7): "))

    # Set up turtle
    screen = turtle.Screen()
    screen.title("Recursive Tree")
    screen.bgcolor("white")

    t = turtle.Turtle()
    t.hideturtle()  # Hide the turtle for a cleaner look
    t.speed(1)
    t.left(90)
    t.penup()
    t.goto(0, -250)
    t.pendown()

    draw_branch(t, start_length, angle_left, angle_right, depth, reduction_factor, depth)

    screen.mainloop()

if __name__ == "__main__":
    main()

