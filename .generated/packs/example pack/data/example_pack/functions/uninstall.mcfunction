#Can be called to remove the pack and any trace it was ever installed
scoreboard objectives remove ep_temp
scoreboard objectives remove used_c_stick

tellraw @a [{"text":"The pack "},{"text":"\"example pack\" ","color":"green","hoverEvent":{"action":"show_text","contents":[{"text":"example_pack - ep\nExample pack used for debugging"}]}},{"text":"has been sucessfully unloaded."}]