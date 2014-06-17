class PlaylistItem < ActiveRecord::Base
  include FormattingExtensions

  validates_presence_of :name
  belongs_to :playlist
  belongs_to :actual_object, :polymorphic => true 
  validate :not_infinite

  default_scope { includes(:actual_object) }

  def self.clear_playlists(playlist_items)
    playlist_ids = playlist_items.collect { |pi| pi.playlist_id }.uniq
    playlists_to_clear = []
    playlists_to_clear = playlist_ids.inject([]) do |arr, pi|
      arr << pi
      arr << Playlist.where(id: pi).first.relation_ids
      arr.flatten
    end

    playlists_to_clear.uniq.each do |pid|
      ActionController::Base.expire_page "/playlists/#{pid}.html"
      ActionController::Base.expire_page "/playlists/#{pid}/export.html"
    end
  end

  def clean_type
    actual_object_type.to_s.downcase
  end

  def user
    self.playlist.present? ? self.playlist.user : nil
  end

  def public?
    self.playlist.present? ? self.playlist.public : nil
  end

  def not_infinite
    return true if !self.new_record?
    return true if self.actual_object_type != 'Playlist'
    errors.add(:base, "You can't add a playlist to itself as a playlist item.") if self.actual_object_id == self.playlist_id
    errors.add(:base, "This playlist is already included as a playlist item in the playlist you are attempting to add.") if self.playlist.relation_ids.include?(self.actual_object_id)
  end

  def render_dropdown
    return false if self.actual_object.nil?

    return false if actual_object_type == "TextBlock"

    return true if actual_object_type == "Playlist"

    return true if actual_object_type == "Collage"

    if self.actual_object.respond_to?(:description)
      return true if self.actual_object.description.present?

      return true if self.description != '' && self.description != self.actual_object.description
    end

    return true if self.notes.to_s != '' && self.public_notes

    false
  end
end
