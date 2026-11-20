function CharacterCreationMain.readSavedOutfitFile()
	local retVal = {};
	
	local saveFile = getFileReader(CharacterCreationMain.savefile, true);
	local version = 0
	local line = saveFile:readLine();
	while line ~= nil do
		if luautils.stringStarts(line, "VERSION=") then
			version = tonumber(string.split(line, "=")[2])
		elseif version == OUTFITS_VERSION then
			-- 12WASHERE: custom body-location IDs contain colons.
			-- Only the first colon separates the preset name from its data.
			local separator = string.find(line, ":", 1, true);
			if separator and separator > 1 then
				retVal[string.sub(line, 1, separator - 1)] = string.sub(line, separator + 1);
			end
		end
		line = saveFile:readLine();
	end
	saveFile:close();
	
	return retVal;
end
