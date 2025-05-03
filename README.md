watchdog-fs
(c) 2025 - Juan-Carlos Maureira 

based on python watchdog implements (delayed) actions triggered on filesystem events, handled via promises

Config File
based on ini format

[event label]
path =
event =
type  =
action =

FileSystem Events

FileSystemMovedEvent
FileMovedEvent
DirMovedEvent
FileModifiedEvent
DirModifiedEvent
FileCreatedEvent
FileClosedEvent
DirCreatedEvent
FileDeletedEvent
DirDeletedEvent

Actions
ActionHandler
DelayedActionHandler


