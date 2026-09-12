package ai.flyciv.mc;

import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.server.command.CommandManager;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.text.Text;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class FlycivMod implements ModInitializer {
	public static final String MOD_ID = "flyciv";
	public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);
	private static Colony colony;

	@Override
	public void onInitialize() {
		LOGGER.info("flyciv: colony of frozen fly brains, evolving adapters, wear-roads");
		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> dispatcher.register(
			CommandManager.literal("flyciv")
				.then(CommandManager.literal("start").executes(ctx -> {
					ServerPlayerEntity player = ctx.getSource().getPlayer();
					if (player == null) {
						ctx.getSource().sendError(Text.literal("Need a player."));
						return 0;
					}
					if (colony != null) {
						colony.stop();
					}
					colony = new Colony();
					colony.start(player);
					ctx.getSource().sendFeedback(() -> Text.literal(
						"flyciv started. 4 hero flies + 64 crowd. Gold blocks are wear-roads. Showcase walk is labeled, not emergence."
					), false);
					return 1;
				}))
				.then(CommandManager.literal("stop").executes(ctx -> {
					if (colony != null) {
						colony.stop();
						colony = null;
					}
					ctx.getSource().sendFeedback(() -> Text.literal("flyciv stopped."), false);
					return 1;
				}))
		));
		ServerTickEvents.END_WORLD_TICK.register(world -> {
			if (colony != null && world == colony.world()) {
				colony.tick();
			}
		});
	}
}
