def fixlength(real,target):
	t = real[:target]
	while len(t)<target: t.append(None)
	return t
