# My Notes

The following is a diagram showing how the nodes work together.

![Alt text](svgs/python-2d-game-engine.drawio.svg "Game engine flow")

## Documentation

### constants.py

Everything starts with the constants.py, it is responsible for the following:

- Pg init.
- Define all paths for:
  - Pngs.
  - Jsons.
  - Wavs.
  - Fonts.
- Define constants:
  - Tile size.
  - Fps.
  - Window size.
  - Native size.
  - Native surf and rect.
  - Clock.
  - Events.
  - Font size.
  - Font instance.
  - Quadtree max depth.
  - Mask id to index dict.

---

### game.py

Then we go to Game class.

This class has the following properties:

- Debug flag.
- Debug draw instance.
  - Anyone can use this, remove this before production.
- Resolution.
- Window size, surf
- Y offset, to center the smaller native surf on the window surf
- Input flags for pressed, just pressed and just released for the following:
  - Up.
  - Down.
  - Left.
  - Right.
  - Lmb.
  - Rmb.
  - Mmb.
  - Enter.
  - Pause.
  - Jump.
  - Attack.
- Key bindings
- All existing game actors memory
- All existing game scenes memory
- Sound manager.
  - Anyone can use this.
- Current scene.

This class has the following methods:

- set_resolution
  - Call this to change the game window size, takes value from 1 to 7.
- set_scene
  - Call this to change the game scene, pass in the string key for the memory value.
- event
  - The main loop calls this, this will update the input flags for all to use. Takes the event from the pump.
- reset_just_events
  - Main loop calls this at the end of loop, to reset the just related events.

---

### main.py

Finally the main.py.

This script is responsible for instancing the game. It is responsible for having the main game loop. This is the entry point of the application. Here is what goes on inside the while loop:

- Frame limiting.
- Event pump and passing event to the game instance.
- Draw the game current scene.
- Update the game current scene.
- Draw the FPS on top left using the debug draw of the game property.
- Calling the game debug draw prop.
- Scale the small native surface to the window.
- Update the display.
- Reset the game just related events.

---

### debug_draw.py

This is the debug drawer. Anyone can add things on certain layer and it will draw it on top of everything. This is how you debug draw a text:

```py
debug_draw.add(
        {
            "type": "text",
            "layer": 6,
            "x": 0,
            "y": 0,
            "text": f"fps: {int(CLOCK.get_fps())}",
        }
    )
```

TODO: Add more example to debug draw other things.

How it works, debug draw is simple. It takes an object that has certain shape then it appends it to an array in a certain layer (nested array).

After the current scene draws everything the game will call this and have it draw each layer, once it has done drawing the whole thing will be emptied again. I am not sure if this is efficient or not but it is for debugging only anyways.

There are a total of 6 layers, counting from 0 for you to use. Debug draw will only draw when debug flag is true. By default you can toggle the debug flag with the 0 key. All event related is always going to be taken care of the game class, check its event method and its event flags.

---

### sound_manager.py

TODO: Write a documentation on this.
