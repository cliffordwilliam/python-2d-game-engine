# Imports

I like explicit imports like this:

```python
from constants import CLOCK
from constants import EVENTS
from constants import FPS
from constants import NATIVE_SURF
from constants import NEXT_FRAME
from constants import pg
from nodes.game import Game
from nodes.options_menu import OptionsMenu
```

This is good to me because even if it is long, I know immediately what this script is using by going to the top of the page. Unlike:

- Using wildcards: I do not know what this script uses, I have to manually check with my eyes.
- Importing the whole thing, then I still need to check with my eyes again to see what it uses.
