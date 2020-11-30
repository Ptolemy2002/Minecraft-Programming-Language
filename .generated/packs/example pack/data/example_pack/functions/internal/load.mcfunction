#This function is run when the datapack is loaded.
scoreboard objectives add ep_temp dummy
scoreboard players set example_pack ep_temp 0

#Ensure the game is run in singleplayer
execute as @a run scoreboard players add example_pack ep_temp 1
execute if score example_pack ep_temp matches 2.. run tellraw @a [{"text":"The pack "},{"text":"\"example pack\"","color":"green","hoverEvent":{"action":"show_text","contents":[{"text":"example_pack - ep\nExample pack used for debugging"}]}},{"text":" is only compatible with singleplayer.\nDisabling the pack to avoid unexpected behavior.\nUse "},{"text":"/datapack enable \"file/example pack\"","color":"green","hoverEvent":{"action":"show_text","contents":[{"text":"Click to copy this command to the chat bar."}]},"clickEvent":{"action":"suggest_command","value":"/datapack enable \"file/example pack\""}},{"text":" To reenable."}]
execute if score example_pack ep_temp matches 2.. run datapack disable "file/example pack"
execute store success storage example_pack isCompatible int 1 if score example_pack ep_temp matches ..1




#variable description



#Ensure all required packs are installed.
execute if data storage example_pack {isCompatible:1} store success score example_pack ep_temp run function fake_pack:exists
execute if score example_pack ep_temp matches 0 run tellraw @a {"text":"The required pack "fake_pack" was not detected to exist.\n Disabling to avoid unexpected behavior.","color":"red"}
execute if score example_pack ep_temp matches 0 run datapack disable "file/example pack"
execute store success storage example_pack isCompatible int 1 if score example_pack ep_temp matches 1

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