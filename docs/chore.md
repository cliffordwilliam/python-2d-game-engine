# My Notes

## Commitizen

https://pypi.org/project/commitizen/

## Pre commit

https://medium.com/@0xmatriksh/how-to-setup-git-hooks-pre-commit-commit-msg-in-my-project-11aaec139536

https://github.com/pre-commit/pre-commit/issues/1550g

pre-commit sample-config | out-file .pre-commit-config.yaml -encoding utf8

## Before prod

Look for all instances of # REMOVE IN BUILD, then delete all that is not needed for prod.

## Take note

All names should be snake case no matter what, this makes it so that the data name can be anywhere, in json or in py files.

## Todo

[ ] - Find ways on how to save json to anyone computer for saving and loading feature.
[ ] - Create an editor to generate jsons for animation data.
[ ] - Create the main menu flow, from splash, title, main menu, settings, load and save screen then game.
[ ] - Be able to save and load at any room in World scene.
[x] - Find ways to make type safety a thing here. Check below on how I did it.
[ ] - Update the doc svg, Reason for change is because I cannot import everything at the constants, import when it is needed only. Like Vector and so on.
[ ] - Always read if there are any more TODO.

## Typesafety

```py
# This only import during coding, not runtime
if TYPE_CHECKING:
    from nodes.game import Game


class CreatedBySplashScreen:
    def __init__(self, game: 'Game'):
        self.game = game
```
