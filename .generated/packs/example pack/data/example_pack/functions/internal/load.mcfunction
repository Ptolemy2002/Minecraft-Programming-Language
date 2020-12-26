#This function is run when the datapack is loaded.
scoreboard objectives add ep_temp dummy
scoreboard players set example_pack ep_temp 0

#Ensure the game is run in singleplayer
execute as @a run scoreboard players add example_pack ep_temp 1
execute if score example_pack ep_temp matches 2.. run tellraw @a [{"text":"The pack "},{"text":"\"example pack\"","color":"green","hoverEvent":{"action":"show_text","contents":[{"text":"example_pack - ep\nExample pack used for debugging"}]}},{"text":" is only compatible with singleplayer.\nDisabling the pack to avoid unexpected behavior.\nUse "},{"text":"/datapack enable \"file/example pack\"","color":"green","hoverEvent":{"action":"show_text","contents":[{"text":"Click to copy this command to the chat bar."}]},"clickEvent":{"action":"suggest_command","value":"/datapack enable \"file/example pack\""}},{"text":" To reenable."}]
execute if score example_pack ep_temp matches 2.. run datapack disable "file/example pack"
execute store success storage example_pack isCompatible int 1 if score example_pack ep_temp matches ..1


data modify storage example_pack vars.x set value 1
data modify storage example_pack constants.y set value 3
data modify storage example_pack constants.s set value "hello"
#variable description
data modify storage example_pack vars.str set value "Hi"

data modify storage example_pack constants.fl set value 0.5
#variable "enemies" Initialization index 0
tag @e[type=zombie] add in_example_pack_enemies
#variable "enemies" Initialization index 1
tag someones_username add in_example_pack_enemies
tag @e[sort=nearest,limit=1] add example_pack_e
#Used for listener used:carrot_on_a_stick
scoreboard objectives add used_c_stick used:carrot_on_a_stick

#Run listeners
function example_pack:listeners/load/main/load1

#Uninstall if incompatible
execute if data storage example_pack {isCompatible:1} run tellraw @a [{"text":"The pack "},{"text":"\"example pack\" ","color":"green","hoverEvent":{"action":"show_text","contents":[{"text":"example_pack - ep\nExample pack used for debugging"}]}},{"text":"has been sucessfully (re)loaded."}]
#Uninstall the pack if it is incompatible
execute if data storage example_pack {isCompatible:0} run function example_pack:uninstall

#Start the tick function
execute if score example_pack ep_temp matches 1 run function example_pack:internal/tick