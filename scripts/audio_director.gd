extends Node

var music := AudioStreamPlayer.new()
var effects := AudioStreamPlayer.new()
var voice := AudioStreamPlayer.new()
var enabled := true

func _ready() -> void:
	music.bus = "Music"
	effects.bus = "SFX"
	voice.bus = "Voice"
	add_child(music)
	add_child(effects)
	add_child(voice)
	var path := "res://assets/generated/audio/cloud_sea.wav"
	if ResourceLoader.exists(path):
		music.stream = load(path)
		music.finished.connect(music.play)
		music.play()

func speak(id: String) -> void:
	voice.stop()
	var path := "res://assets/generated/voices/%s.wav" % id
	if enabled and ResourceLoader.exists(path):
		voice.stream = load(path)
		voice.play()

func effect(id: String = "page") -> void:
	var path := "res://assets/generated/audio/%s.wav" % id
	if ResourceLoader.exists(path):
		effects.stream = load(path)
		effects.play()
