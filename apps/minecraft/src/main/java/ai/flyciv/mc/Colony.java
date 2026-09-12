package ai.flyciv.mc;

import net.minecraft.block.BlockState;
import net.minecraft.block.Blocks;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.attribute.EntityAttributes;
import net.minecraft.entity.passive.BeeEntity;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.util.math.BlockPos;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

/**
 * Live Minecraft colony. Showcase choreography (4 heroes walk the axes, crowd mills,
 * gold = wear). Labeled as designed rules — not a full MaleCNS LIF in this jar.
 */
public final class Colony {
	private static final int SIZE = 48;
	private static final int ARM = 12;
	private static final int HEROES = 4;
	private static final int CROWD = 64;
	private static final int STEPS_PER_GEN = 36;
	private static final int TICKS_PER_STEP = 4;
	private static final int GENERATIONS = 6;

	private ServerWorld world;
	private BlockPos origin;
	private int tick;
	private int step;
	private int generation = 1;
	private boolean trainer;
	private boolean childSpawned;
	private boolean stopped;
	private final List<Flyer> flyers = new ArrayList<>();

	private static final int[][] DIR = {{0, -1}, {1, 0}, {0, 1}, {-1, 0}};

	public ServerWorld world() {
		return world;
	}

	public void start(ServerPlayerEntity player) {
		this.world = player.getServerWorld();
		this.origin = player.getBlockPos().down();
		buildPlatform();
		spawnFlies();
		this.tick = 0;
		this.step = 0;
		this.generation = 1;
		this.trainer = false;
		this.childSpawned = false;
		this.stopped = false;
		broadcast("gen 1 · trainer OFF · gold appears where they walk");
	}

	public void stop() {
		stopped = true;
		for (Flyer f : flyers) {
			if (f.bee != null && !f.bee.isRemoved()) {
				f.bee.discard();
			}
		}
		flyers.clear();
	}

	public void tick() {
		if (stopped || world == null) {
			return;
		}
		tick++;
		if (tick % TICKS_PER_STEP != 0) {
			keepBees();
			return;
		}
		step++;
		if (step > STEPS_PER_GEN) {
			step = 1;
			generation++;
			if (generation == 3 && !trainer) {
				trainer = true;
				BlockPos nest = origin;
				world.setBlockState(nest, Blocks.SEA_LANTERN.getDefaultState());
				world.setBlockState(nest.up(), Blocks.LIGHT_BLUE_STAINED_GLASS.getDefaultState());
				broadcast("TRAINER ON · the city is paying to write child adapters");
			}
			if (generation == 4 && trainer && !childSpawned) {
				spawnChild();
				broadcast("child born · a new fly at the nest");
			}
			if (generation > GENERATIONS) {
				broadcast("done · 6 generations. Roads are wear. Not a living fly.");
				keepBees();
				return;
			}
		}
		for (Flyer f : flyers) {
			stepFlyer(f);
		}
		keepBees();
		if (step == 1) {
			broadcast("gen " + generation + (trainer ? " · trainer ON" : " · trainer OFF"));
		}
	}

	private void buildPlatform() {
		int y = origin.getY();
		int ox = origin.getX();
		int oz = origin.getZ();
		BlockState floor = Blocks.BLACK_CONCRETE.getDefaultState();
		for (int dx = -SIZE / 2; dx <= SIZE / 2; dx++) {
			for (int dz = -SIZE / 2; dz <= SIZE / 2; dz++) {
				world.setBlockState(new BlockPos(ox + dx, y, oz + dz), floor);
			}
		}
		world.setBlockState(origin, Blocks.LIGHT_BLUE_CONCRETE.getDefaultState());
		world.setBlockState(origin.up(), Blocks.LIGHT_BLUE_STAINED_GLASS.getDefaultState());
		world.setBlockState(new BlockPos(ox, y, oz - ARM), Blocks.LIME_CONCRETE.getDefaultState());
		world.setBlockState(new BlockPos(ox + ARM, y, oz), Blocks.LIME_CONCRETE.getDefaultState());
		world.setBlockState(new BlockPos(ox, y, oz + ARM), Blocks.LIME_CONCRETE.getDefaultState());
		world.setBlockState(new BlockPos(ox - ARM, y, oz), Blocks.LIME_CONCRETE.getDefaultState());
	}

	private void spawnFlies() {
		for (int i = 0; i < HEROES; i++) {
			flyers.add(spawnOne(0, 0, i, true, false, 0.7));
		}
		for (int i = 0; i < CROWD; i++) {
			int rx = (i * 7) % 9 - 4;
			int rz = (i * 3) % 9 - 4;
			flyers.add(spawnOne(rx, rz, i % 4, false, false, 0.38));
		}
	}

	private void spawnChild() {
		Flyer child = spawnOne(0, 0, 0, true, true, 0.85);
		flyers.add(child);
		childSpawned = true;
	}

	private Flyer spawnOne(int lx, int lz, int heading, boolean hero, boolean child, double scale) {
		BeeEntity bee = EntityType.BEE.create(world);
		if (bee == null) {
			throw new IllegalStateException("could not create bee");
		}
		bee.setAiDisabled(true);
		bee.setSilent(true);
		bee.setInvulnerable(true);
		bee.setPersistent();
		bee.setBaby(false);
		String name = child ? "flyciv child" : (hero ? "flyciv hero" : "flyciv");
		Formatting color = child ? Formatting.GOLD : (hero ? Formatting.GOLD : Formatting.GRAY);
		bee.setCustomName(Text.literal(name).formatted(color));
		bee.setCustomNameVisible(hero || child);
		var attr = bee.getAttributeInstance(EntityAttributes.GENERIC_SCALE);
		if (attr != null) {
			attr.setBaseValue(scale);
		}
		double x = origin.getX() + lx + 0.5;
		double y = origin.getY() + 1.1;
		double z = origin.getZ() + lz + 0.5;
		bee.refreshPositionAndAngles(x, y, z, heading * 90f, 0f);
		world.spawnEntity(bee);
		Flyer f = new Flyer();
		f.bee = bee;
		f.lx = lx;
		f.lz = lz;
		f.heading = heading;
		f.axis = heading;
		f.hero = hero;
		f.child = child;
		return f;
	}

	private void stepFlyer(Flyer f) {
		if (f.bee == null || f.bee.isRemoved()) {
			return;
		}
		if (f.hero) {
			int dist = Math.abs(f.lx) + Math.abs(f.lz);
			if (dist >= ARM) {
				f.heading = (f.axis + 2) % 4;
			} else if (dist == 0) {
				f.heading = f.axis;
			}
			f.lx += DIR[f.heading][0];
			f.lz += DIR[f.heading][1];
			wear(f.lx, f.lz);
		} else {
			if (Math.abs(f.lx) + Math.abs(f.lz) > 6) {
				if (f.lx != 0) {
					f.lx += f.lx > 0 ? -1 : 1;
				} else if (f.lz != 0) {
					f.lz += f.lz > 0 ? -1 : 1;
				}
			} else {
				f.heading = (f.heading + (f.lx + f.lz + step) % 2) % 4;
				f.lx += DIR[f.heading][0];
				f.lz += DIR[f.heading][1];
				if (Math.abs(f.lx) > 6) {
					f.lx = Integer.compare(0, f.lx) * 6;
				}
				if (Math.abs(f.lz) > 6) {
					f.lz = Integer.compare(0, f.lz) * 6;
				}
			}
		}
		double x = origin.getX() + f.lx + 0.5;
		double y = origin.getY() + 1.15;
		double z = origin.getZ() + f.lz + 0.5;
		f.bee.refreshPositionAndAngles(x, y, z, f.heading * 90f, 0f);
		f.bee.setVelocity(0, 0, 0);
	}

	private void wear(int lx, int lz) {
		BlockPos pos = origin.add(lx, 0, lz);
		if (pos.equals(origin)) {
			return;
		}
		var cur = world.getBlockState(pos);
		if (cur.isOf(Blocks.LIME_CONCRETE) || cur.isOf(Blocks.SEA_LANTERN) || cur.isOf(Blocks.LIGHT_BLUE_CONCRETE)) {
			return;
		}
		world.setBlockState(pos, Blocks.GOLD_BLOCK.getDefaultState());
	}

	private void keepBees() {
		for (Flyer f : flyers) {
			if (f.bee != null && !f.bee.isRemoved()) {
				f.bee.setVelocity(0, 0, 0);
				f.bee.setAiDisabled(true);
			}
		}
	}

	private void broadcast(String msg) {
		if (world.getServer() == null) {
			return;
		}
		world.getServer().getPlayerManager().broadcast(Text.literal("[flyciv] " + msg).formatted(Formatting.AQUA), false);
	}

	static final class Flyer {
		BeeEntity bee;
		int lx;
		int lz;
		int heading;
		int axis;
		boolean hero;
		boolean child;
	}
}
