from  etabs_interface import *
def create_grid_system(sapmodel, story_heights, x_coordinates, y_coordinates):
    number_of_stories = len(story_heights)
    typical_story_height = story_heights[1]
    bottom_story_height = story_heights[0]
    number_of_lines_x = len(x_coordinates)
    number_of_iines_y = len(y_coordinates)
    spacing_x = x_coordinates[1]
    spacing_y = y_coordinates[1]

    ret = sapmodel.InitializeNewModel(6)
    if ret == 0:
        print("Function InitializeNewModel was successful")
    else:
        print("Error running function InitializeNewModel")

    ret = sapmodel.File.NewGridOnly(number_of_stories, typical_story_height, bottom_story_height,
                                    number_of_lines_x, number_of_lines_x, spacing_x, spacing_y)
    if ret == 0:
        print("Function NewGridOnly was successful")
    else:
        print("Error running function NewGridOnly")

       # Generate a nested list of the points resulting from the intersection of x and y coordinates
    grid_points = [[(x, y) for y in y_coordinates] for x in x_coordinates]

    # The output nested list has dimensions: len(x_coordinates) x len(y_coordinates)
    return grid_points
     
