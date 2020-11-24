#This function is run when the datapack is loaded.
scoreboard objectives add ep_temp dummy
scoreboard players set example_pack ep_temp 0
#Ensure the game is run in singleplayer
execute as @a run scoreboard players add example_pack ep_temp 1
execute if score example_pack ep_temp matches 2.. run tellraw @a [{"text":"The pack "},{"text":"\"example pack\"","color":"green","hoverEvent":{"action":"show_text","contents":[{"text":"example_pack - ep\nExample pack used for debugging"}]}},{"text":" is only compatible with singleplayer.\nDisabling the pack to avoid unexpected behavior.\nUse "},{"text":"/datapack enable \"file/example pack\"","color":"green","hoverEvent":{"action":"show_text","contents":[{"text":"Click to copy this command to the chat bar."}]},"clickEvent":{"action":"suggest_command","value":"/datapack enable \"file/example pack\""}},{"text":" To reenable."}]
execute if score example_pack ep_temp matches 2.. run datapack disable "file/example pack"
execute store success storage ep isCompatible int if score example_pack example_pack_t matches ..1



#variable description



#Used for listener used:carrot_on_a_stick
scoreboard objectives add used_c_stick used:carrot_on_a_stick
function example_pack:listeners/load/main/load1
execute store result score example_pack ep_t run data get storage example_pack isCompatible
execute if score example_pack ep_t matches 1 run tellraw @a [{"text":"The pack "},{"text":"\"example pack\" ","color":"green","hoverEvent":{"action":"show_text","contents":[{"text":"example_pack - ep\nExample pack used for debugging"}]}},{"text":"has been sucessfully (re)loaded."}]
#Uninstall the pack if it is incompatible
execute if score example_pack ep_t matches 0 run function example_pack:uninstall