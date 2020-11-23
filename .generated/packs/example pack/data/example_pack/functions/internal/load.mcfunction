#This function is run when the datapack is loaded.
scoreboard objectives add example_pack_temp dummy
execute as @a run scoreboard players add example_pack example_pack_temp 1
execute if score example_pack example_pack_temp matches 2.. run tellraw @a [{"text":"The pack "},{"text":"example pack","color":"green","hoverEvent":{"action":"show_text","contents":[{"text":"example_pack
Example pack used for debugging"}]}},{"text":" is only compatible with singleplayer.\nDisabling it."}]
execute if score example_pack example_pack_temp matches 2.. run scoreboard objectives remove example_pack_temp
execute if score example_pack example_pack_temp matches 2.. run datapack disable example_pack
#Should fail and stop this function
execute if score example_pack example_pack_temp matches 2.. as THIS_GUY_IS_FAKE



#variable description



#Used for listener used:carrot_on_a_stick
scoreboard objectives add used_c_stick used:carrot_on_a_stick
function example_pack:listeners/load/main/load1
tellraw @a [{"text":"The pack "},{"text":"\"example pack\" ","color":"green","hoverEvent":{"action":"show_text","contents":[{"text":"example_pack\nExample pack used for debugging"}]}},{"text":"has been sucessfully (re)loaded."}]