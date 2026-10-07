# BuildingGadgets2
A recreation of my very first mod - Building Gadgets. This time with less DireCode. Or more, depending on how you look at it....

## NeoForge 26.2 port

This fork ports Direwolf20's Building Gadgets 2 **1.4.6** to Minecraft **26.2**,
NeoForge **26.2.0.88**, and **Java 25**. The original `buildinggadgets2` mod ID,
items, recipes, data components, and saved-data format are retained. The existing
upstream branch name `21.6` is retained; it does not describe this fork's Minecraft version.

Install `buildinggadgets2-1.4.6-zedo.1+26.2.jar` in **both** the server and each
client. Replace any other Building Gadgets 2 jar. Curios **16.0.0+26.2** is optional
at runtime and included in the development runs. AE2 and Patchouli integration
were already disabled in the upstream 26.1.2 source and are not restored here.
The upstream MIT license and author attribution are preserved.

### Build and test

```sh
./gradlew clean build
./gradlew runClientData runServerData
```

The distributable jar is in `build/libs/`; the `-sources.jar` is not a mod to
install. `build` runs the NeoForge-backed JUnit regression suite for block states,
negative coordinates, template palettes, rotation, block-entity NBT, SavedData,
and packet codecs (16 checks). The data generators cover models, language,
recipes, loot tables, and tags.

For isolated gameplay testing, `runClient` and `runServer` use `runs/client/`
and `runs/server/`. Configure your own test server and accept Minecraft's EULA
before running it. `./gradlew -PtestServer=127.0.0.1:25595 runClient` connects the
test player to that endpoint. These profiles do not share a launcher instance
or a production world.

### Gameplay verification — 2026-10-07

Tested with a real NeoForge client and dedicated server, Curios 16, and the
[Minecraft Automation NeoForge port](https://github.com/zedoCN/minecraft-automation).
The client used Apple M3 Pro/OpenGL, with server-authoritative block and inventory
readback rather than relying only on the client cache.

- Block selection, build, and undo; survival construction used one stone and
  50 FE, and undo returned the stone while consuming another 50 FE.
- All six construction animation modes; exchange and destruction with undo.
- Copy/paste of stone, transparent glass, and directional stairs; 90-degree
  rotation changed both placement coordinates and stair facing.
- Cut/paste moved a chest containing seven diamonds, preserved its contents,
  and consumed the cut data so a second paste did not duplicate it.
- Copy coordinates and destruction settings screens; template save/name,
  material list, and the 3D template preview displayed correctly.
- Authenticated automation RPC, screenshots, Java scratch, and block-hit
  right-click fallback were exercised against the real client.

The G radial menu reads GLFW's physical key state, so a synthetic
`input.keyAction` cannot keep it open. This inherited behavior is not treated
as a successful physical-key test. The complete TECH pack, its Vulkan renderer,
large builds, mod-specific machine contents, and third-party protection mods
still need their own gameplay acceptance. No production server was restarted
as part of these isolated tests.
