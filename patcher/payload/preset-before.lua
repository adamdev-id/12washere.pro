function CharacterCreationMain.readSavedOutfitFile()
	local retVal = {};
	
	local saveFile = getFileReader(CharacterCreationMain.savefile, true);
	local version = 0
	local line = saveFile:readLine();
	while line ~= nil do
		if luautils.stringStarts(line, "VERSION=") then
			version = tonumber(string.split(line, "=")[2])
		elseif version == OUTFITS_VERSION then
			local s = luautils.split(line, ":");
			retVal[s[1]] = s[2];
		end
		line = saveFile:readLine();
	end
	saveFile:close();
	
	return retVal;
end
